from aiogram.filters.state import State, StatesGroup


class AdminStats(StatesGroup):
    input_password = State()
    add_managers = State()
    edit_password = State()
    transfer_admin = State()


class UserStats(StatesGroup):
    new_deadline = State()
