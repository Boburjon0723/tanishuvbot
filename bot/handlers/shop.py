from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    get_premium_plans_keyboard,
    get_shop_items_keyboard,
    get_shop_menu_keyboard,
)
from config.shop import ANIMATION_CONTENT, STICKER_CONTENT, get_item
from database.connections import Database
from database.queries import get_user, get_user_items, is_user_premium

router = Router()


@router.message(F.text == "🛍 Do'kon")
async def shop_menu(message: Message, db: Database) -> None:
    if not await get_user(db, message.from_user.id):
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return

    await message.answer(
        "🛍 <b>JuftPari Do'koni</b>\n\n"
        "• <b>Premium</b> — xabar yozish va ustun ko'rinish\n"
        "• <b>Stikerlar</b> — noyob stikerlar yuborish\n"
        "• <b>Animatsiyalar</b> — maxsus effektlar\n\n"
        "To'lov: karta + chek skrinshoti",
        parse_mode="HTML",
        reply_markup=get_shop_menu_keyboard(),
    )


@router.callback_query(F.data == "shop:back")
async def shop_back(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            "🛍 <b>JuftPari Do'koni</b>\n\nBo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=get_shop_menu_keyboard(),
        )


@router.callback_query(F.data == "shop:premium")
async def shop_premium(callback: CallbackQuery, db: Database) -> None:
    await callback.answer()
    if await is_user_premium(db, callback.from_user.id):
        if callback.message:
            await callback.message.edit_text("✅ Sizda allaqachon Premium bor!")
        return
    if callback.message:
        await callback.message.edit_text(
            "⭐ <b>Premium tariflar</b>\n\n"
            "• Xabar yozish\n"
            "• Qidiruvda ustun joy\n"
            "• ⭐ belgisi",
            parse_mode="HTML",
            reply_markup=get_premium_plans_keyboard(),
        )


@router.callback_query(F.data == "shop:stickers")
async def shop_stickers(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            "🎨 <b>Noyob stikerlar</b>\n\n"
            "Sotib olgach chatda stiker yuborasiz.",
            parse_mode="HTML",
            reply_markup=get_shop_items_keyboard("sticker"),
        )


@router.callback_query(F.data == "shop:animations")
async def shop_animations(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            "✨ <b>Animatsiyalar</b>\n\n"
            "Maxsus effektlarni chatda yuboring.",
            parse_mode="HTML",
            reply_markup=get_shop_items_keyboard("animation"),
        )


@router.callback_query(F.data == "shop:inventory")
async def shop_inventory(callback: CallbackQuery, db: Database) -> None:
    await callback.answer()
    items = await get_user_items(db, callback.from_user.id)
    premium = await is_user_premium(db, callback.from_user.id)

    lines = []
    if premium:
        lines.append("⭐ Premium — faol")
    for key in items:
        item = get_item(key)
        if item:
            lines.append(f"{item.emoji} {item.name}")

    text = (
        "📦 <b>Sizning buyumlaringiz:</b>\n\n" + "\n".join(lines)
        if lines
        else "📦 Hozircha buyumlar yo'q.\nDo'kondan xarid qiling!"
    )
    if callback.message:
        await callback.message.edit_text(
            text, parse_mode="HTML", reply_markup=get_shop_menu_keyboard()
        )
