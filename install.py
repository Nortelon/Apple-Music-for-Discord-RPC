"""
Apple Music Discord RPC - Kurulum
Arka planda calistirir ve Windows baslangicindan itibaren otomatik baslatir.
"""
import os
import sys
import subprocess
import winreg

APP_NAME = "AppleMusicDiscordRPC"
DIR     = os.path.dirname(os.path.abspath(__file__))
MAIN    = os.path.join(DIR, "main.py")

def _find_pythonw() -> str:
    # python.exe'nin yanindaki pythonw.exe'yi bul
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    # PATH'te ara
    import shutil
    found = shutil.which("pythonw")
    if found:
        return found
    raise FileNotFoundError("pythonw.exe bulunamadi.")

def _kill_existing():
    pid_file = os.path.join(os.environ.get("TEMP", DIR), "apple_music_rpc.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file) as f:
                pid = f.read().strip()
            subprocess.run(["taskkill", "/pid", pid, "/f"], capture_output=True)
        except Exception:
            pass

def install():
    pythonw = _find_pythonw()
    cmd = f'"{pythonw}" "{MAIN}"'

    # Windows Registry: kullanici girisi yapinca otomatik calistir
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE,
    )
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(key)
    print(f"[OK] Baslangica eklendi.")

    # Varsa onceki ornegi kapat
    _kill_existing()

    # Hemen arka planda baslat (konsol penceresi yok)
    subprocess.Popen(
        [pythonw, MAIN],
        creationflags=0x08000000,  # CREATE_NO_WINDOW
        close_fds=True,
        cwd=DIR,
    )
    print(f"[OK] Arka planda baslatildi.")
    print(f"\nDurdurmak / kaldirmak icin:  python uninstall.py")

if __name__ == "__main__":
    install()
