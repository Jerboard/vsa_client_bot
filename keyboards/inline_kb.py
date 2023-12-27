from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import db


# клавиатура для задач
def get_task_kb(task_id, chat_id, message_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📄 Контекст', callback_data=f'context:{chat_id}:{message_id}')],
        [
            InlineKeyboardButton(text='✅ Готово', callback_data=f'close_task:done:{task_id}'),
            InlineKeyboardButton(text='🗑 Отменить', callback_data=f'close_task:cancel:{task_id}'),
            InlineKeyboardButton(text='📆 Перенести', callback_data=f'edit_deadline:{task_id}'),
            InlineKeyboardButton(text='❌ Ошибка', callback_data=f'close_task:error:{task_id}')]
    ])


# кнопка отменить действие и скинуть статус
def get_cancel_action_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Отменить', callback_data='cancel_action')]])


# панель администратора
def get_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton (text='Добавить чат', callback_data='edit_chat:add')],
        [InlineKeyboardButton (text='Удалить чат', callback_data='edit_chat:del')],
        [InlineKeyboardButton(text='Назначить менеджера', callback_data='admin_manager_1:add')],
        [InlineKeyboardButton(text='Удалить менеджера', callback_data='admin_manager_1:del')],
        [InlineKeyboardButton(text='Сменить пароль администратора', callback_data='edit_password')],
        [InlineKeyboardButton(text='Передать статус администратора', callback_data='transfer_admin')],
    ])


# Список менеджеров на удаление
def get_delete_managers_kb(managers: tuple[db.UserRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data='cancel_action')

    for manager in managers:
        kb.button(text=f'@{manager.username}', callback_data=f'delete_manager:{manager.id}')

    kb.adjust (1, True)
    return kb.as_markup()


# Список чатов на удаление
def get_delete_chats_kb(chats: tuple[db.ChatRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data='cancel_action')

    for chat in chats:
        kb.button(text=chat.chat_title[:50], callback_data=f'delete_chat:{chat.chat_id}')

    kb.adjust (1, True)
    return kb.as_markup()


# Подтвердить удаление
def get_delete_chats_confirm_kb(chat_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button (text='🔙 Назад', callback_data='edit_chat:del')
    kb.button (text='🗑 Подтвердить', callback_data=f'confirm_del_chat:{chat_id}')
    kb.adjust (1, True)
    return kb.as_markup()
