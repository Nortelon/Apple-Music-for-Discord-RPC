import asyncio
import os
import time
import sys
import logging
from pypresence import AioPresence, ActivityType, StatusDisplayType, InvalidID, DiscordNotFound

from media import get_apple_music_info, MediaState
from artwork import get_track_info
from config import Config

# Arka planda calisirken log dosyasina yaz
_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rpc.log")
_PID_FILE = os.path.join(os.environ.get("TEMP", ""), "apple_music_rpc.pid")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# PID dosyasini yaz (uninstall.py bu processi bulur)
with open(_PID_FILE, "w") as _f:
    _f.write(str(os.getpid()))
log = logging.getLogger(__name__)


async def main_loop(rpc: AioPresence, config: Config):
    last_track = None
    last_artwork_url = None
    last_track_url = None

    log.info("Apple Music izleniyor... (Cikis icin CTRL+C)")

    while True:
        try:
            state: MediaState = await get_apple_music_info()

            if state is None or not state.is_playing:
                if last_track is not None:
                    await rpc.clear()
                    log.info("Muzik durdu, presence temizlendi.")
                    last_track = None
                    last_artwork_url = None
                    last_track_url = None
                await asyncio.sleep(config.poll_interval)
                continue

            track_changed = (
                last_track is None
                or last_track.title != state.title
                or last_track.artist != state.artist
            )

            if track_changed:
                log.info(f"Simdi caliniyor: {state.artist} - {state.title}")
                info = await get_track_info(state.title, state.artist, state.album)
                last_artwork_url = info.artwork_url
                last_track_url = info.apple_music_url
                last_track = state
                log.info(f"Track URL: {last_track_url}")

            now = time.time()
            start = int(now - state.position_seconds)
            end = int(start + state.duration_seconds) if state.duration_seconds > 0 else None

            buttons = None

            await rpc.update(
                activity_type=ActivityType.LISTENING,
                status_display_type=StatusDisplayType.DETAILS,
                name="Apple Music",
                details=state.title,
                state=state.artist,
                large_image=last_artwork_url or config.fallback_image,
                small_image=config.apple_music_icon,
                small_text="Apple Music",
                start=start,
                end=end,
                buttons=buttons,
            )

        except Exception as e:
            log.warning(f"Presence guncelleme hatasi: {e}")

        await asyncio.sleep(config.poll_interval)


async def run():
    config = Config.load()

    rpc = AioPresence(config.discord_client_id)
    try:
        await rpc.connect()
        log.info("Discord RPC baglantisi kuruldu.")
    except DiscordNotFound:
        log.error("Discord acik degil! Lutfen Discord'u baslatin.")
        sys.exit(1)
    except InvalidID:
        log.error("Gecersiz Discord Client ID. config.json dosyasini kontrol edin.")
        sys.exit(1)

    try:
        await main_loop(rpc, config)
    except KeyboardInterrupt:
        log.info("Kapatiliyor...")
    finally:
        try:
            await rpc.clear()
            rpc.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(run())
