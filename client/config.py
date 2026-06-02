import json
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

DEFAULT_CONFIG = {
    "server_url": "http://127.0.0.1:8000",
    "serial_port": "COM3",
    "baud_rate": 9600,
}


def normalize_server_url(url: str) -> str:
    cleaned = url.strip()
    cleaned = re.sub(r"^(https?://)\s+", r"\1", cleaned, flags=re.IGNORECASE)
    return cleaned.rstrip("/")


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            config = {**DEFAULT_CONFIG, **data}
            config["server_url"] = normalize_server_url(config["server_url"])
            return config
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
