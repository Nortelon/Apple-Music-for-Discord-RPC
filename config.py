"""
Yapilandirma - config.json dosyasindan okunur.
"""
import json
import os
import sys
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "discord_client_id": "1448000316137017434",
    "poll_interval": 1,
    "fallback_image": "apple_music_logo",
    "apple_music_icon": "apple_music_logo",
}


@dataclass
class Config:
    discord_client_id: str
    poll_interval: int
    fallback_image: str
    apple_music_icon: str

    @staticmethod
    def load() -> "Config":
        if not os.path.exists(CONFIG_FILE):
            # config.example.json varsa kopyala, yoksa varsayilani olustur
            example = os.path.join(os.path.dirname(CONFIG_FILE), "config.example.json")
            template = DEFAULT_CONFIG
            if os.path.exists(example):
                with open(example, "r", encoding="utf-8") as f:
                    template = json.load(f)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            log.error(
                "config.json olusturuldu.\n"
                "Lutfen 'discord_client_id' alanina Discord Application ID'nizi girin\n"
                "ve tekrar calistirin.  ->  discord.com/developers/applications"
            )
            sys.exit(1)

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        client_id = data.get("discord_client_id", "")
        if not client_id or client_id == "BURAYA_CLIENT_ID_YAZ":
            log.error(
                "config.json icinde 'discord_client_id' ayarlanmamis!\n"
                "Adimlar icin README'yi okuyun."
            )
            sys.exit(1)

        return Config(
            discord_client_id=client_id,
            poll_interval=int(data.get("poll_interval", 1)),
            fallback_image=data.get("fallback_image", "apple_music_logo"),
            apple_music_icon=data.get("apple_music_icon", "apple_music_logo"),
        )
