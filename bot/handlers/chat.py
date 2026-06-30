from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    get_chat_reply_keyboard,
    get_gifts_keyboard,
    get_main_menu,
    get_matches_chat_keyboard,
    get_premium_plans_keyboard,
    get_reply_inline_keyboard,
)
from bot.states.chat import ChatStates
from config.settings import get_settings
from config.shop import ANIMATION_CONTENT
from database.connections import Database
from database.queries import (
    are_matched,
    get_user,
    get_user_items,
    get_user_matches,
    is_user_premium,
)

from bot.keyboards.menu import MAIN_MENU_TEXTS


async def can_use_chat(db: Database, user_id: int) -> bool:
    settings = get_settings()
    if not settings.chat_requires_premium:
        return True
    return await is_user_premium(db, user_id)


async def can_message_partner(db: Database, viewer_id: int, partner_id: int) -> bool:
    settings = get_settings()
    if not settings.chat_requires_match:
        return True
    return await are_matched(db, viewer_id, partner_id)


@router.message(F.text == "💬 Xabarlar")
async def open_chats(message: Message, db: Database) -> None:
    user = await get_user(db, message.from_user.id)
    if not user:
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return

    if not await can_use_chat(db, message.from_user.id):
        await message.answer(
            "💬 <b>Xabar yozish uchun Premium kerak!</b>\n\n"
            "⭐ Premium yoki 🛍 Do'kondan sotib oling.",
            parse_mode="HTML",
            reply_markup=get_premium_plans_keyboard(),
        )
        return

    matches = await get_user_matches(db, message.from_user.id)
    if not matches:
        await message.answer(
            "Hozircha mosliklar yo'q.\n"
            "🔍 Sherik qidirishda anketa ostidagi <b>💬 Xabar</b> tugmasini bosing!",
            parse_mode="HTML",
        )
        return

    await message.answer(
        "Kimga xabar yozmoqchisiz?",
        reply_markup=get_matches_chat_keyboard(matches),
    )


@router.callback_query(F.data == "chat:cancel")
async def chat_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.edit_text("Bekor qilindi.")


@router.callback_query(F.data.startswith("chat:open:"))
async def chat_open(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    partner_id = int(callback.data.split(":")[2])
    viewer_id = callback.from_user.id

    if not await can_use_chat(db, viewer_id):
        await callback.answer("Premium kerak!", show_alert=True)
        if callback.message:
            await callback.message.answer(
                "💬 <b>Xabar yozish uchun Premium kerak!</b>\n\n"
                "⭐ Premium sotib oling — keyin xabar yoza olasiz.",
                parse_mode="HTML",
                reply_markup=get_premium_plans_keyboard(),
            )
        return

    if not await can_message_partner(db, viewer_id, partner_id):
        await callback.answer(
            "Avval like bosing — mos tushgandan keyin yozasiz.", show_alert=True
        )
        return

    partner = await get_user(db, partner_id)
    if not partner:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    await state.set_state(ChatStates.typing)
    await state.update_data(partner_id=partner_id)

    items = await get_user_items(db, viewer_id)
    gifts_kb = get_gifts_keyboard(items)

    await callback.answer()
    if callback.message:
        extra = "\n\n🎨 Stiker/animatsiya tugmalaridan ham foydalaning!" if gifts_kb else ""
        await callback.message.answer(
            f"💬 <b>{partner['name']}</b> ga xabar yozing.\n\n"
            f"Matn yuboring yoki stiker tanlang.{extra}\n"
            "Yopish: ❌ Chatni yopish",
            parse_mode="HTML",
            reply_markup=get_chat_reply_keyboard(),
        )
        if gifts_kb:
            await callback.message.answer("🎁 Sizning stikerlaringiz:", reply_markup=gifts_kb)


@router.message(F.text == "❌ Chatni yopish")
async def close_chat(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current != ChatStates.typing:
        return
    await state.clear()
    await message.answer("Chat yopildi.", reply_markup=get_main_menu())


@router.message(ChatStates.typing, F.text, ~F.text.in_(MAIN_MENU_TEXTS))
async def send_chat_message(
    message: Message, state: FSMContext, db: Database
) -> None:
    if not await can_use_chat(db, message.from_user.id):
        await state.clear()
        await message.answer("Xabar yozish uchun Premium kerak.")
        return

    data = await state.get_data()
    partner_id = data.get("partner_id")
    if not partner_id:
        await state.clear()
        await message.answer("Chat topilmadi. Qayta urinib ko'ring.")
        return

    if not await can_message_partner(db, message.from_user.id, partner_id):
        await state.clear()
        await message.answer("Bu foydalanuvchiga yozib bo'lmaydi.")
        return

    sender = await get_user(db, message.from_user.id)
    if not sender:
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Bo'sh xabar yuborib bo'lmaydi.")
        return
    if len(text) > 1000:
        await message.answer("Xabar 1000 belgidan oshmasligi kerak.")
        return

    try:
        await message.bot.send_message(
            partner_id,
            f"💬 <b>Yangi xabar — {sender['name']}</b>\n\n{text}",
            parse_mode="HTML",
            reply_markup=get_reply_inline_keyboard(message.from_user.id),
        )
    except Exception:
        await message.answer(
            "Xabar yetkazilmadi. Foydalanuvchi botni bloklagan yoki demo profil."
        )
        return

    await message.answer("✅ Xabar yuborildi!")


@router.callback_query(F.data.startswith("gift:sticker:"))
async def send_sticker_gift(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    if await state.get_state() != ChatStates.typing:
        await callback.answer("Avval chatni oching", show_alert=True)
        return
    if not await can_use_chat(db, callback.from_user.id):
        await callback.answer("Premium kerak!", show_alert=True)
        return

    emoji = callback.data.split(":")[2]
    data = await state.get_data()
    partner_id = data.get("partner_id")
    sender = await get_user(db, callback.from_user.id)
    if not partner_id or not sender:
        return

    try:
        await callback.bot.send_message(
            partner_id,
            f"🎁 <b>{sender['name']}</b> dan stiker:\n\n{emoji}",
            parse_mode="HTML",
            reply_markup=get_reply_inline_keyboard(callback.from_user.id),
        )
    except Exception:
        await callback.answer("Yuborilmadi", show_alert=True)
        return
    await callback.answer("Stiker yuborildi!")


@router.callback_query(F.data.startswith("gift:anim:"))
async def send_animation_gift(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    if await state.get_state() != ChatStates.typing:
        await callback.answer("Avval chatni oching", show_alert=True)
        return
    if not await can_use_chat(db, callback.from_user.id):
        await callback.answer("Premium kerak!", show_alert=True)
        return

    anim_key = callback.data.split(":")[2]
    content = ANIMATION_CONTENT.get(anim_key, "✨")
    data = await state.get_data()
    partner_id = data.get("partner_id")
    sender = await get_user(db, callback.from_user.id)
    if not partner_id or not sender:
        return

    try:
        await callback.bot.send_message(
            partner_id,
            f"✨ <b>{sender['name']}</b> dan animatsiya:\n\n{content}",
            parse_mode="HTML",
            reply_markup=get_reply_inline_keyboard(callback.from_user.id),
        )
    except Exception:
        await callback.answer("Yuborilmadi", show_alert=True)
        return
    await callback.answer("Animatsiya yuborildi!")
