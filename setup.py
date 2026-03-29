"""
Kurulum ve yapilandirma yardimcisi.
Calistir: python setup.py
"""
import subprocess
import sys
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def install_deps():
    print("[1/3] pypresence yukleniyor...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "pypresence>=4.3.0"
    ])
    print("      Basariyla yuklendi.\n")


def configure():
    print("[2/3] Discord uygulama yapilandirmasi")
    print("=" * 55)
    print("1. https://discord.com/developers/applications  adresine gir")
    print("2. 'New Application' -> isme 'Apple Music' yaz")
    print("3. Sol menu: Rich Presence -> Art Assets")
    print("   'apple_music_logo' adıyla Apple Music logosunu yukle (PNG)")
    print("4. Sol menu: General Information -> APPLICATION ID'yi kopyala")
    print("=" * 55)
    client_id = input("\nDiscord Application ID: ").strip()

    if not client_id.isdigit():
        print("HATA: Application ID sadece rakamlardan olusmalidir!")
        sys.exit(1)

    config = {
        "discord_client_id": client_id,
        "poll_interval": 5,
        "fallback_image": "apple_music_logo",
        "apple_music_icon": "apple_music_logo"
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"\n      config.json kaydedildi.\n")


def test_media():
    print("[3/3] Apple Music baglantisi test ediliyor...")
    import asyncio
    from media import get_apple_music_info

    state = asyncio.run(get_apple_music_info())
    if state:
        status = "CALINIYOR" if state.is_playing else "DURAKLATILDI"
        print(f"      [{status}] {state.artist} - {state.title}")
    else:
        print("      Simdi calınan icerik yok (Apple Music'i acip sarki cal).")

    print("\n" + "=" * 55)
    print("Kurulum tamamlandi! Baslatmak icin:")
    print("  python main.py")
    print("=" * 55)


if __name__ == "__main__":
    print("\nApple Music Discord Rich Presence - Kurulum\n")
    install_deps()
    configure()
    test_media()
