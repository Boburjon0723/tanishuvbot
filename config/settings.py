import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    min_age: int = 18
    payment_currency: str = "UZS"
    payment_card: str = ""
    payment_card_holder: str = ""
    chat_requires_premium: bool = True
    chat_requires_match: bool = False


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN .env faylida ko'rsatilmagan")

    db_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'dating_bot.db'}")

    return Settings(
        bot_token=token,
        database_url=db_url,
        min_age=int(os.getenv("MIN_AGE", "18")),
        payment_currency=os.getenv("PAYMENT_CURRENCY", "UZS"),
        payment_card=os.getenv("PAYMENT_CARD", ""),
        payment_card_holder=os.getenv("PAYMENT_CARD_HOLDER", ""),
        chat_requires_premium=os.getenv("CHAT_REQUIRES_PREMIUM", "true").lower() == "true",
        chat_requires_match=os.getenv("CHAT_REQUIRES_MATCH", "false").lower() == "true",
    )
