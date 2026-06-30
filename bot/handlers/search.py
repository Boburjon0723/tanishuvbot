import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    get_main_menu,
    get_reply_inline_keyboard,
    get_search_keyboard,
)
from database.connections import Database
from database.queries import (
    add_action,
    create_match,
    get_next_profile,
    get_user,
    has_mutual_like,
)

router = Router()
logger = logging.getLogger(__name__)

GENDER_LABELS = {"male": "Erkak", "female": "Ayol"}
TARGET_LABELS = {"male": "Erkaklar", "female": "Ayollar", "all": "Hammasi"}


def format_profile(user: dict) -> str:
    return (
        f"👤 <b>{user['name']}</b>, {user['age']} yosh\n"
        f"⚧ Jins: {GENDER_LABELS.get(user['gender'], user['gender'])}\n"
        f"📍 {user['city']}\n\n"
        f"{user['bio'] or '—'}"
    )


async def show_next_profile(
    message: Message, state: FSMContext, db: Database, viewer_id: int
) -> None:
    try:
        viewer = await get_user(db, viewer_id)
        if not viewer:
            await message.answer("Avval ro'yxatdan o'ting: /start")
            return

        if not bool(viewer.get("is_active")):
            await message.answer(
                "Profilingiz muzlatilgan. Qidiruv uchun profilni faollashtiring.",
                reply_markup=get_main_menu(),
            )
            return

        profile = await get_next_profile(db, viewer_id, viewer["target_gender"])
        if not profile:
            await state.update_data(current_profile_id=None)
            await message.answer(
                "😔 Hozircha mos anketalar tugadi.\nKeyinroq qayta urinib ko'ring!",
                reply_markup=get_main_menu(),
            )
            return

        await state.update_data(current_profile_id=profile["telegram_id"])
        try:
            await message.answer_photo(
                photo=profile["photo_id"],
                caption=format_profile(profile),
                reply_markup=get_search_keyboard(profile["telegram_id"]),
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.exception("Anketa rasmini yuborib bo'lmadi: %s", exc)
            await message.answer(
                format_profile(profile),
                reply_markup=get_search_keyboard(profile["telegram_id"]),
                parse_mode="HTML",
            )
    except Exception as exc:
        logger.exception("Qidiruvda xato: %s", exc)
        await message.answer(
            "Qidiruvda xatolik yuz berdi. Iltimos, /start bosing va qayta urinib ko'ring.",
            reply_markup=get_main_menu(),
        )


@router.message(F.text == "🔍 Sherik qidirish")
async def start_search(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    logger.info("Qidiruv boshlandi: user_id=%s", message.from_user.id)
    await show_next_profile(message, state, db, message.from_user.id)


@router.callback_query(F.data == "search:stop")
async def stop_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(current_profile_id=None)
    await callback.message.answer("Qidiruv to'xtatildi.", reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data.in_({"search:like", "search:dislike"}))
async def process_search_action(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    data = await state.get_data()
    target_id = data.get("current_profile_id")
    if not target_id:
        await callback.answer("Anketa topilmadi. Qayta qidiring.", show_alert=True)
        return

    viewer_id = callback.from_user.id
    action_type = "like" if callback.data == "search:like" else "dislike"
    await add_action(db, viewer_id, target_id, action_type)

    if action_type == "like":
        if await has_mutual_like(db, viewer_id, target_id):
            created = await create_match(db, viewer_id, target_id)
            if created:
                viewer = await get_user(db, viewer_id)
                target = await get_user(db, target_id)
                match_text = (
                    "🎉 <b>Tabriklaymiz! Sizda moslik bor!</b>\n\n"
                    f"{format_profile(target)}"
                )
                await callback.message.answer(
                    match_text + "\n\n💬 Xabar yozish uchun <b>💬 Xabar</b> tugmasini bosing.",
                    parse_mode="HTML",
                    reply_markup=get_reply_inline_keyboard(target_id),
                )
                if callback.bot and target:
                    try:
                        await callback.bot.send_message(
                            target_id,
                            "🎉 <b>Tabriklaymiz! Sizda moslik bor!</b>\n\n"
                            f"{format_profile(viewer)}\n\n"
                            "💬 Javob berish uchun tugmani bosing.",
                            parse_mode="HTML",
                            reply_markup=get_reply_inline_keyboard(viewer_id),
                        )
                    except Exception:
                        pass

    await callback.answer()
    await show_next_profile(callback.message, state, db, viewer_id)
