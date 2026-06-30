from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.inline import TERMS_KEYBOARD, get_main_menu
from bot.states.registration import RegistrationStates
from database.connections import Database
from database.queries import get_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    user = await get_user(db, message.from_user.id)

    if user:
        await message.answer(
            f"Salom, {user['name']}! 👋\n\nAsosiy menyudan kerakli bo'limni tanlang.",
            reply_markup=get_main_menu(),
        )
        return

    await state.set_state(RegistrationStates.terms)
    await message.answer(
        "👋 Salom! Bu tanishuv botiga xush kelibsiz.\n\n"
        "Davom etish uchun bot qoidalarini qabul qiling:\n"
        "• Faqat 18 yoshdan kattalar ro'yxatdan o'tishi mumkin\n"
        "• Hurmatli muloqot qiling\n"
        "• Noto'g'ri ma'lumot bermang",
        reply_markup=TERMS_KEYBOARD,
    )
