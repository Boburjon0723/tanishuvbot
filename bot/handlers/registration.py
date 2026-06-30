from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot.keyboards.inline import (
    GENDER_KEYBOARD,
    SKIP_BIO_KEYBOARD,
    TARGET_GENDER_KEYBOARD,
    TERMS_KEYBOARD,
    get_main_menu,
)
from bot.states.registration import RegistrationStates
from config.settings import get_settings
from database.connections import Database
from database.queries import create_user, get_user, update_user

router = Router()
settings = get_settings()

GENDER_LABELS = {"male": "Erkak", "female": "Ayol"}
TARGET_LABELS = {"male": "Erkaklar", "female": "Ayollar", "all": "Hammasi"}


@router.callback_query(RegistrationStates.terms, F.data == "terms:accept")
async def terms_accept(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegistrationStates.name)
    await callback.message.edit_text("Ismingizni kiriting:")
    await callback.answer()


@router.callback_query(RegistrationStates.terms, F.data == "terms:decline")
async def terms_decline(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Botdan foydalanish uchun qoidalarni qabul qilishingiz kerak.\n"
        "Qayta urinish uchun /start bosing."
    )
    await callback.answer()


@router.message(RegistrationStates.name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("Ism 2 dan 50 gacha belgidan iborat bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(name=name)
    await state.set_state(RegistrationStates.age)
    await message.answer("Yoshingizni kiriting (faqat raqam, 18+):")


@router.message(RegistrationStates.age)
async def process_age(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Yosh faqat raqam bo'lishi kerak. Qayta kiriting:")
        return
    age = int(text)
    if age < settings.min_age or age > 100:
        await message.answer(f"Yosh {settings.min_age} dan 100 gacha bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(age=age)
    await state.set_state(RegistrationStates.gender)
    await message.answer("Jinsingizni tanlang:", reply_markup=GENDER_KEYBOARD)


@router.callback_query(RegistrationStates.gender, F.data.startswith("gender:"))
async def process_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    await state.set_state(RegistrationStates.target_gender)
    await callback.message.edit_text(
        "Kimni qidirmoqchisiz?",
        reply_markup=TARGET_GENDER_KEYBOARD,
    )
    await callback.answer()


@router.callback_query(RegistrationStates.target_gender, F.data.startswith("target:"))
async def process_target_gender(callback: CallbackQuery, state: FSMContext) -> None:
    target = callback.data.split(":")[1]
    await state.update_data(target_gender=target)
    await state.set_state(RegistrationStates.city)
    await callback.message.edit_text("Qaysi shaharda yashaysiz? Shahar nomini yozing:")
    await callback.answer()


@router.message(RegistrationStates.city)
async def process_city(message: Message, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if len(city) < 2 or len(city) > 80:
        await message.answer("Shahar nomi juda qisqa yoki uzun. Qayta kiriting:")
        return
    await state.update_data(city=city)
    await state.set_state(RegistrationStates.photo)
    await message.answer(
        "Endi o'zingizning yaxshi ko'rinadigan rasmingizni yuboring 📸",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(RegistrationStates.photo, F.photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(RegistrationStates.bio)
    await message.answer(
        "O'zingiz haqingizda qisqacha yozing (yoki «O'tkazib yuborish» tugmasini bosing):",
        reply_markup=SKIP_BIO_KEYBOARD,
    )


@router.message(RegistrationStates.photo)
async def process_photo_invalid(message: Message) -> None:
    await message.answer("Iltimos, rasm yuboring 📸")


@router.message(RegistrationStates.bio)
async def process_bio(message: Message, state: FSMContext, db: Database) -> None:
    text = (message.text or "").strip()
    bio = "" if text == "⏭ O'tkazib yuborish" else text
    if len(bio) > 500:
        await message.answer("Bio 500 belgidan oshmasligi kerak. Qisqartiring:")
        return
    await _save_profile(message, state, db, bio)


async def _save_profile(
    message: Message, state: FSMContext, db: Database, bio: str
) -> None:
    data = await state.get_data()
    user_id = message.from_user.id

    existing = await get_user(db, user_id)
    if existing:
        await update_user(
            db,
            user_id,
            name=data["name"],
            age=data["age"],
            gender=data["gender"],
            target_gender=data["target_gender"],
            city=data["city"],
            photo_id=data["photo_id"],
            bio=bio,
            is_active=1,
        )
    else:
        await create_user(
            db,
            telegram_id=user_id,
            name=data["name"],
            age=data["age"],
            gender=data["gender"],
            target_gender=data["target_gender"],
            city=data["city"],
            photo_id=data["photo_id"],
            bio=bio,
        )

    await state.clear()
    await message.answer(
        "✅ Profil muvaffaqiyatli saqlandi!\n\nAsosiy menyudan foydalaning:",
        reply_markup=get_main_menu(),
    )


@router.callback_query(F.data == "profile:edit")
async def edit_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegistrationStates.name)
    await callback.message.answer("Profilni yangilash. Ismingizni kiriting:")
    await callback.answer()
