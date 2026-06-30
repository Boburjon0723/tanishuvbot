from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    get_main_menu,
    get_payment_cancel_keyboard,
    get_premium_plans_keyboard,
)
from bot.states.payment import PaymentStates
from config.settings import get_settings
from config.shop import get_item, get_premium_items
from database.connections import Database
from database.queries import activate_premium, get_user, grant_item, is_user_premium

router = Router()

PREMIUM_BENEFITS = (
    "Imtiyozlar:\n"
    "• 💬 Xabar yozish\n"
    "• Qidiruvda ustun joy\n"
    "• Premium ⭐ belgisi"
)


def format_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " so'm"


def format_card(card: str) -> str:
    digits = "".join(c for c in card if c.isdigit())
    if len(digits) == 16:
        return " ".join(digits[i : i + 4] for i in range(0, 16, 4))
    return card


@router.message(F.text == "⭐ Premium")
async def premium_menu(message: Message, db: Database) -> None:
    user = await get_user(db, message.from_user.id)
    if not user:
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return

    if await is_user_premium(db, message.from_user.id):
        until = user.get("premium_until")
        await message.answer(
            f"✅ Sizda allaqachon <b>Premium</b> bor!\n"
            f"Tugash sanasi: <b>{until}</b>",
            parse_mode="HTML",
        )
        return

    plans_text = "\n".join(
        f"• <b>{p.name}</b> — {format_price(p.price)}" for p in get_premium_items()
    )
    await message.answer(
        f"⭐ <b>JuftPari Premium</b>\n\n"
        f"{plans_text}\n\n"
        f"{PREMIUM_BENEFITS}\n\n"
        "🛍 Boshqa buyumlar: <b>🛍 Do'kon</b>",
        parse_mode="HTML",
        reply_markup=get_premium_plans_keyboard(),
    )


@router.callback_query(F.data == "pay:premium")
async def pay_premium_legacy(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Tarifni tanlang:",
            reply_markup=get_premium_plans_keyboard(),
        )


@router.callback_query(F.data == "pay:cancel")
async def pay_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Bekor qilindi")
    if callback.message:
        await callback.message.edit_text("To'lov bekor qilindi.")


@router.callback_query(F.data.startswith("pay:buy:"))
async def select_buy(callback: CallbackQuery, state: FSMContext) -> None:
    item_key = callback.data.split(":")[2]
    await _start_payment(callback, state, item_key)


@router.callback_query(F.data.startswith("pay:plan:"))
async def select_plan_legacy(callback: CallbackQuery, state: FSMContext) -> None:
    item_key = callback.data.split(":")[2]
    await _start_payment(callback, state, item_key)


async def _start_payment(
    callback: CallbackQuery, state: FSMContext, item_key: str
) -> None:
    item = get_item(item_key)
    settings = get_settings()

    if not item:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    if not settings.payment_card:
        await callback.answer("Karta sozlanmagan", show_alert=True)
        return

    await state.set_state(PaymentStates.waiting_receipt)
    await state.update_data(item_key=item.key, item_category=item.category)

    holder = (
        f"\n👤 Egasi: <b>{settings.payment_card_holder}</b>"
        if settings.payment_card_holder
        else ""
    )

    await callback.answer()
    if callback.message:
        await callback.message.answer(
            f"💳 <b>To'lov ma'lumotlari</b>\n\n"
            f"Mahsulot: <b>{item.emoji} {item.name}</b>\n"
            f"Summa: <b>{format_price(item.price)}</b>\n\n"
            f"Karta raqami:\n<code>{format_card(settings.payment_card)}</code>"
            f"{holder}\n\n"
            "1️⃣ Kartaga to'lov qiling\n"
            "2️⃣ <b>Chek skrinshoti</b> ni rasm sifatida yuboring\n\n"
            "Chek kelgach buyum <b>avtomatik</b> beriladi ✅",
            parse_mode="HTML",
            reply_markup=get_payment_cancel_keyboard(),
        )


@router.message(F.text == "❌ To'lovni bekor qilish")
async def cancel_payment(message: Message, state: FSMContext) -> None:
    if await state.get_state() != PaymentStates.waiting_receipt:
        return
    await state.clear()
    settings = get_settings()
    await message.answer(
        "To'lov bekor qilindi.",
        reply_markup=get_main_menu(),
    )


@router.message(PaymentStates.waiting_receipt, F.photo | F.document)
async def receive_receipt(
    message: Message, state: FSMContext, db: Database
) -> None:
    if message.document and message.document.mime_type and not message.document.mime_type.startswith("image/"):
        await message.answer("Iltimos, chekni <b>rasm</b> sifatida yuboring.", parse_mode="HTML")
        return

    data = await state.get_data()
    item_key = data.get("item_key", "30d")
    item = get_item(item_key)

    if not item:
        await message.answer("Mahsulot topilmadi.")
        await state.clear()
        return

    try:
        if item.category == "premium":
            until = await activate_premium(db, message.from_user.id, item.days)
            until_text = until.strftime("%d.%m.%Y %H:%M")
            result = (
                f"⭐ <b>Premium faollashtirildi!</b>\n"
                f"Tugash: <b>{until_text}</b>\n\n"
                "Endi 💬 xabar yozishingiz mumkin!"
            )
        else:
            await grant_item(db, message.from_user.id, item.key)
            result = (
                f"{item.emoji} <b>{item.name}</b> sizniki bo'ldi!\n\n"
                "Chatda stiker/animatsiya tugmalaridan foydalaning."
            )
    except Exception:
        await message.answer("Xatolik yuz berdi. Qayta urinib ko'ring.")
        return

    await state.clear()
    settings = get_settings()
    await message.answer(
        f"🎉 <b>Chek qabul qilindi!</b>\n\n{result}",
        parse_mode="HTML",
        reply_markup=get_main_menu(),
    )


@router.message(PaymentStates.waiting_receipt)
async def receipt_invalid(message: Message) -> None:
    await message.answer(
        "Chekni <b>rasm</b> sifatida yuboring 📸\n"
        "Bekor: ❌ To'lovni bekor qilish",
        parse_mode="HTML",
    )
