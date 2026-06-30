from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

TERMS_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul qilaman", callback_data="terms:accept"),
            InlineKeyboardButton(text="❌ Rad etaman", callback_data="terms:decline"),
        ]
    ]
)

GENDER_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Erkak", callback_data="gender:male"),
            InlineKeyboardButton(text="👩 Ayol", callback_data="gender:female"),
        ]
    ]
)

TARGET_GENDER_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Erkaklar", callback_data="target:male"),
            InlineKeyboardButton(text="👩 Ayollar", callback_data="target:female"),
        ],
        [InlineKeyboardButton(text="🌐 Hammasi", callback_data="target:all")],
    ]
)

SEARCH_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Like", callback_data="search:like"),
            InlineKeyboardButton(text="👎 Dislike", callback_data="search:dislike"),
        ],
        [InlineKeyboardButton(text="💤 To'xtatish", callback_data="search:stop")],
    ]
)


def get_search_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❤️ Like", callback_data="search:like"),
                InlineKeyboardButton(text="👎 Dislike", callback_data="search:dislike"),
                InlineKeyboardButton(
                    text="💬 Xabar", callback_data=f"chat:open:{profile_id}"
                ),
            ],
            [InlineKeyboardButton(text="💤 To'xtatish", callback_data="search:stop")],
        ]
    )


def get_profile_keyboard(is_premium: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="profile:edit")],
        [
            InlineKeyboardButton(text="⏸ Muzlatish", callback_data="profile:freeze"),
            InlineKeyboardButton(text="▶️ Faollashtirish", callback_data="profile:activate"),
        ],
    ]
    if not is_premium:
        rows.append(
            [InlineKeyboardButton(text="⭐ Premium sotib olish", callback_data="pay:premium")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


PROFILE_KEYBOARD = get_profile_keyboard()


def get_premium_plans_keyboard() -> InlineKeyboardMarkup:
    from config.shop import get_premium_items

    rows = []
    for item in get_premium_items():
        price = f"{item.price:,}".replace(",", " ")
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"⭐ {item.name} — {price} so'm",
                    callback_data=f"pay:buy:{item.key}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="pay:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_shop_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Premium", callback_data="shop:premium")],
            [InlineKeyboardButton(text="🎨 Stikerlar", callback_data="shop:stickers")],
            [InlineKeyboardButton(text="✨ Animatsiyalar", callback_data="shop:animations")],
            [InlineKeyboardButton(text="📦 Mening buyumlarim", callback_data="shop:inventory")],
        ]
    )


def get_shop_items_keyboard(category: str) -> InlineKeyboardMarkup:
    from config.shop import get_animation_items, get_sticker_items

    items = get_sticker_items() if category == "sticker" else get_animation_items()
    rows = []
    for item in items:
        price = f"{item.price:,}".replace(",", " ")
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{item.emoji} {item.name} — {price} so'm",
                    callback_data=f"pay:buy:{item.key}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="shop:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_gifts_keyboard(item_keys: list[str]) -> InlineKeyboardMarkup | None:
    from config.shop import ANIMATION_CONTENT, STICKER_CONTENT

    rows: list[list[InlineKeyboardButton]] = []
    sticker_row: list[InlineKeyboardButton] = []

    for key in item_keys:
        if key in STICKER_CONTENT:
            for emoji in STICKER_CONTENT[key][:3]:
                sticker_row.append(
                    InlineKeyboardButton(
                        text=emoji, callback_data=f"gift:sticker:{emoji}"
                    )
                )
                if len(sticker_row) == 3:
                    rows.append(sticker_row)
                    sticker_row = []
        if key in ANIMATION_CONTENT:
            item = ANIMATION_CONTENT[key]
            label = item.split()[0]
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"✨ {label}", callback_data=f"gift:anim:{key}"
                    )
                ]
            )

    if sticker_row:
        rows.append(sticker_row)

    if not rows:
        return None
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_premium_keyboard() -> InlineKeyboardMarkup:
    return get_premium_plans_keyboard()


def get_payment_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ To'lovni bekor qilish")]],
        resize_keyboard=True,
    )


def get_chat_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Chatni yopish")]],
        resize_keyboard=True,
    )


def get_matches_chat_keyboard(matches: list) -> InlineKeyboardMarkup:
    rows = []
    for match in matches:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💬 {match['name']}, {match['age']}",
                    callback_data=f"chat:open:{match['telegram_id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="chat:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_reply_inline_keyboard(partner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Javob berish",
                    callback_data=f"chat:open:{partner_id}",
                )
            ]
        ]
    )


SKIP_BIO_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⏭ O'tkazib yuborish")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Sherik qidirish")],
            [
                KeyboardButton(text="👤 Mening profilim"),
                KeyboardButton(text="💕 Mosliklarim"),
            ],
            [KeyboardButton(text="⭐ Premium"), KeyboardButton(text="🛍 Do'kon")],
            [KeyboardButton(text="💬 Xabarlar")],
        ],
        resize_keyboard=True,
    )
