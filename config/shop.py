from dataclasses import dataclass


@dataclass(frozen=True)
class ShopItem:
    key: str
    name: str
    price: int
    category: str  # premium, sticker, animation
    days: int = 0
    emoji: str = ""


SHOP_CATALOG: list[ShopItem] = [
    ShopItem("3d", "Premium 3 kun", 9900, "premium", 3, "⭐"),
    ShopItem("7d", "Premium 1 hafta", 19900, "premium", 7, "⭐"),
    ShopItem("30d", "Premium 1 oy", 29900, "premium", 30, "⭐"),
    ShopItem("pack_love", "💋 Sevgi stikerlari", 4900, "sticker", 0, "💋"),
    ShopItem("pack_fun", "😂 Kulgi stikerlari", 3900, "sticker", 0, "😂"),
    ShopItem("pack_romance", "🌹 Romantika stikerlari", 5900, "sticker", 0, "🌹"),
    ShopItem("anim_sparkle", "✨ Yulduz animatsiya", 2900, "animation", 0, "✨"),
    ShopItem("anim_hearts", "💕 Yuraklar animatsiya", 2900, "animation", 0, "💕"),
    ShopItem("anim_fire", "🔥 Olov animatsiya", 2900, "animation", 0, "🔥"),
]

STICKER_CONTENT: dict[str, list[str]] = {
    "pack_love": ["💋", "❤️‍🔥", "💕", "😍", "🥰", "💖"],
    "pack_fun": ["😂", "🤣", "😜", "🎉", "🔥", "👏"],
    "pack_romance": ["🌹", "💐", "✨", "🦋", "💫", "🌙"],
}

ANIMATION_CONTENT: dict[str, str] = {
    "anim_sparkle": "✨ ⭐ ✨ ⭐ ✨",
    "anim_hearts": "💕 💗 💕 💗 💕",
    "anim_fire": "🔥 🔥 🔥 🔥 🔥",
}


def get_item(key: str) -> ShopItem | None:
    return next((i for i in SHOP_CATALOG if i.key == key), None)


def get_premium_items() -> list[ShopItem]:
    return [i for i in SHOP_CATALOG if i.category == "premium"]


def get_sticker_items() -> list[ShopItem]:
    return [i for i in SHOP_CATALOG if i.category == "sticker"]


def get_animation_items() -> list[ShopItem]:
    return [i for i in SHOP_CATALOG if i.category == "animation"]
