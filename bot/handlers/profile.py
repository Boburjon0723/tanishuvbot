from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_profile_keyboard
from database.connections import Database
from database.queries import get_user, is_user_premium, set_user_active

router = Router()

GENDER_LABELS = {"male": "Erkak", "female": "Ayol"}
TARGET_LABELS = {"male": "Erkaklar", "female": "Ayollar", "all": "Hammasi"}


def format_own_profile(user: dict, premium: bool = False) -> str:
    status = "✅ Faol" if user["is_active"] else "⏸ Muzlatilgan"
    premium_line = "⭐ Premium" if premium else "Oddiy"
    return (
        f"👤 <b>Mening profilim</b>\n\n"
        f"Ism: {user['name']}\n"
        f"Yosh: {user['age']}\n"
        f"Jins: {GENDER_LABELS.get(user['gender'], user['gender'])}\n"
        f"Qidiruv: {TARGET_LABELS.get(user['target_gender'], user['target_gender'])}\n"
        f"Shahar: {user['city']}\n"
        f"Holat: {status}\n"
        f"Obuna: {premium_line}\n\n"
        f"{user['bio'] or '—'}"
    )


@router.message(F.text == "👤 Mening profilim")
async def show_profile(message: Message, db: Database) -> None:
    user = await get_user(db, message.from_user.id)
    if not user:
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return
    premium = await is_user_premium(db, message.from_user.id)
    await message.answer_photo(
        photo=user["photo_id"],
        caption=format_own_profile(user, premium),
        reply_markup=get_profile_keyboard(premium),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "profile:freeze")
async def freeze_profile(callback: CallbackQuery, db: Database) -> None:
    await set_user_active(db, callback.from_user.id, False)
    await callback.answer("Profil muzlatildi")
    user = await get_user(db, callback.from_user.id)
    if user:
        premium = await is_user_premium(db, callback.from_user.id)
        await callback.message.edit_caption(
            caption=format_own_profile(user, premium),
            reply_markup=get_profile_keyboard(premium),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "profile:activate")
async def activate_profile(callback: CallbackQuery, db: Database) -> None:
    await set_user_active(db, callback.from_user.id, True)
    await callback.answer("Profil faollashtirildi")
    user = await get_user(db, callback.from_user.id)
    if user:
        premium = await is_user_premium(db, callback.from_user.id)
        await callback.message.edit_caption(
            caption=format_own_profile(user, premium),
            reply_markup=get_profile_keyboard(premium),
            parse_mode="HTML",
        )
