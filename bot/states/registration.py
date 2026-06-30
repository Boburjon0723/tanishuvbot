from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    terms = State()
    name = State()
    age = State()
    gender = State()
    target_gender = State()
    city = State()
    photo = State()
    bio = State()
