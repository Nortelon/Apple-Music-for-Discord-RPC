"""
Windows SMTC ile Apple Music bilgisini alir.
Arka planda surekli calisan bir PowerShell watcher kullanir:
 - PowerShell sadece bir kez baslar, her saniye JSON dosyasini gunceller
 - Python dosyayi okur -> PowerShell startup gecikmesi yok
"""
import asyncio
import atexit
import json
import os
import subprocess
from dataclasses import dataclass
from typing import Optional

_TMP_FILE = os.path.join(
    os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp")),
    "apple_music_smtc.json",
)

_CREATE_NO_WINDOW = 0x08000000

# Her saniye JSON dosyasini guncelleyen surekli PowerShell dongusu
_PS_LOOP = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$_asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $t) { $task = $_asTask.MakeGenericMethod([Type[]]@($t)).Invoke($null, @($op)); $task.Wait() | Out-Null; return $task.Result }
$ManagerType = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime]
$PropsType   = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties, Windows.Media.Control, ContentType=WindowsRuntime]
$null        = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionPlaybackStatus, Windows.Media.Control, ContentType=WindowsRuntime]
$PLAYING     = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionPlaybackStatus]::Playing
$OUT_FILE    = $env:APPLE_MUSIC_TMP
$UTF8        = New-Object System.Text.UTF8Encoding($false)

while ($true) {
    try {
        $manager = Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) $ManagerType
        $target  = $null
        foreach ($s in $manager.GetSessions()) { if ($s.SourceAppUserModelId -match 'AppleMusic|iTunes|apple') { $target = $s; break } }
        if ($null -eq $target) { $cur = $manager.GetCurrentSession(); if ($null -ne $cur -and $cur.GetPlaybackInfo().PlaybackStatus -eq $PLAYING) { $target = $cur } }
        if ($null -eq $target) {
            [System.IO.File]::WriteAllText($OUT_FILE, '{}', $UTF8)
        } else {
            $props    = Await ($target.TryGetMediaPropertiesAsync()) $PropsType
            $playback = $target.GetPlaybackInfo()
            $timeline = $target.GetTimelineProperties()
            $out = [ordered]@{
                title       = "$($props.Title)"
                artist      = "$($props.Artist)"
                albumArtist = "$($props.AlbumArtist)"
                album       = "$($props.AlbumTitle)"
                isPlaying   = ($playback.PlaybackStatus -eq $PLAYING)
                position    = [math]::Round($timeline.Position.TotalSeconds, 2)
                duration    = [math]::Round($timeline.EndTime.TotalSeconds, 2)
            }
            [System.IO.File]::WriteAllText($OUT_FILE, ($out | ConvertTo-Json -Compress), $UTF8)
        }
    } catch {
        try { [System.IO.File]::WriteAllText($OUT_FILE, '{}', $UTF8) } catch {}
    }
    Start-Sleep -Milliseconds 1000
}
"""

_watcher_proc: Optional[subprocess.Popen] = None


def _start_watcher() -> None:
    global _watcher_proc
    if _watcher_proc and _watcher_proc.poll() is None:
        return
    env = {**os.environ, "APPLE_MUSIC_TMP": _TMP_FILE}
    _watcher_proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", _PS_LOOP],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_CREATE_NO_WINDOW,
        env=env,
    )
    atexit.register(_stop_watcher)


def _stop_watcher() -> None:
    if _watcher_proc and _watcher_proc.poll() is None:
        _watcher_proc.terminate()


def _clean_artist(artist: str, album_artist: str) -> str:
    if album_artist and album_artist != artist:
        return album_artist
    for sep in (" \u2014 ", " \u2013 ", " \u2012 "):
        if sep in artist:
            return artist.split(sep)[0].strip()
    return artist


@dataclass
class MediaState:
    title: str
    artist: str
    album: str
    is_playing: bool
    position_seconds: float
    duration_seconds: float


def _read_state() -> Optional[MediaState]:
    try:
        with open(_TMP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            return None
        raw_artist   = data.get("artist", "")
        album_artist = data.get("albumArtist", "").strip()
        return MediaState(
            title=data.get("title", ""),
            artist=_clean_artist(raw_artist, album_artist),
            album=data.get("album", ""),
            is_playing=bool(data.get("isPlaying", False)),
            position_seconds=float(data.get("position", 0)),
            duration_seconds=float(data.get("duration", 0)),
        )
    except Exception:
        return None


async def get_apple_music_info() -> Optional[MediaState]:
    _start_watcher()
    # Watcher ilk baslarken dosya yoktur, kisa bekle
    if not os.path.exists(_TMP_FILE):
        await asyncio.sleep(2)
    return await asyncio.to_thread(_read_state)
