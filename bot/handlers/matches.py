from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.inline import get_reply_inline_keyboard
from database.connections import Database
from database.queries import get_user_matches

router = Router()

GENDER_LABELS = {"male": "Erkak", "female": "Ayol"}


def format_match(user: dict) -> str:
    return (
        f"👤 <b>{user['name']}</b>, {user['age']} yosh\n"
        f"⚧ {GENDER_LABELS.get(user['gender'], user['gender'])}\n"
        f"📍 {user['city']}\n\n"
        f"{user['bio'] or '—'}"
    )


@router.message(F.text == "💕 Mosliklarim")
async def show_matches(message: Message, db: Database) -> None:
    matches = await get_user_matches(db, message.from_user.id)
    if not matches:
        await message.answer("Hozircha mosliklar yo'q. Qidiruvni boshlang! 🔍")
        return

    await message.answer(
        f"Sizda <b>{len(matches)}</b> ta moslik bor:",
        parse_mode="HTML",
    )
    for match in matches:
        await message.answer_photo(
            photo=match["photo_id"],
            caption=format_match(match),
            reply_markup=get_reply_inline_keyboard(match["telegram_id"]),
            parse_mode="HTML",
        )
