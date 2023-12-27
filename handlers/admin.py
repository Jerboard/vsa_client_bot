import logging
import asyncio

from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from init import dp, bot, UB_USERNAME
import db
from keyboards import inline_kb as kb
from utils.func import check_link_in_entities
from utils.redis_utils import edit_chat_filter
from bot_user.functions import add_chat_bot, leave_chat_bot


async def get_start_admin_screen(chat_id: int) -> None:
    text = '<b>Действия администратора:</b>'
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=kb.get_admin_kb ())


# @dp.message_handler(state='input_password')
@dp.message(StateFilter('input_password'))
async def input_password(msg: Message, state: FSMContext):
    await msg.delete()
    if await db.check_admin_password(user_id=msg.from_user.id, check_password=msg.text):
        await state.clear()
        # await db.add_transfer_admin(msg.from_user.username)
        await get_start_admin_screen(msg.chat.id)

    else:
        data = await state.get_data()
        tries = data['try'] - 1
        if tries > 0:
            await msg.answer(f'❌ Неверный пароль. Осталось попыток {tries}')
            await state.update_data(data={'try': tries})
        else:
            await state.clear()
            await msg.answer(f'❌ Неверный пароль')


# перенос дедлайна
@dp.callback_query(lambda cb: cb.data.startswith('admin_manager_1'))
async def admin_manager_1(cb: CallbackQuery, state: FSMContext):
    user = await db.get_admin_info (cb.from_user.id)
    if not user.status:
        await cb.message.answer('❌ У вас нет доступа')
    else:
        cb_data = cb.data.split(':')
        if cb_data[1] == 'add':
            await state.set_state('add_managers')

            text = f'Отправьте username менеджера(ов).\n' \
                   f'Вы можете отправить один username или списком через пробел или запятую. ' \
                   f'Все пользователи получат статус менеджера.\n\n' \
                   f'❗️Важно:\n' \
                   f'Менеджерами могут быть только пользователи активировавшие бот.\n' \
                   f'Вы можете назначит менеджером любого пользователя, но пока он не активирует бот, бот не будет ' \
                   f'воспринимать полученные от него задачи.\n' \
                   f'Чтобы активировать бот пользователь должен пройти по ссылке <code>https://t.me/vsa_chat_bot</code> ' \
                   f'и нажать кнопку "Старт" в нижней части экрана.'

            await cb.message.answer(text, reply_markup=kb.get_cancel_action_button(), parse_mode='html')

        elif cb_data[1] == 'del':
            text = 'Для удаления менеджера нажмите на кнопку с его username.\n' \
                   'Менеджер получит сообщение о изменении статуса'

            managers = await db.get_managers_admin (cb.from_user.id)
            await cb.message.answer(text, reply_markup=kb.get_delete_managers_kb(managers))


# добавляет менеджеров
# @dp.message(state='add_managers')
@dp.message(StateFilter('add_managers'))
async def add_managers(msg: Message, state: FSMContext):
    await state.clear()
    text = msg.text.replace(',', '').replace('@', '')
    new_managers = text.split(' ')
    for manager in new_managers:
        user_id = await db.add_new_manager(manager.strip())
        if user_id is not None:
            try:
                await bot.send_message(user_id, 'Вы получили статус менеджера')
            except Exception as ex:
                print(ex)

    await msg.answer('✅ Менеджеры назначены')


# удаление менеджера
# @dp.callback_query(text_startswith='delete_manager')
@dp.callback_query(lambda cb: cb.data.startswith('delete_manager'))
async def delete_manager(cb: CallbackQuery, state: FSMContext):
    user = await db.get_admin_info (cb.from_user.id)
    if not user.status:
        await cb.message.answer('❌ У вас нет доступа')
    else:
        _, id_user = cb.data.split(':')
        del_manager = await db.delete_manager_status(id_user)
        if del_manager.full_name:
            await cb.answer(f'Менеджер {del_manager.full_name} удалён')
        else:
            await cb.answer (f'Менеджер {del_manager.username} удалён')

        managers = await db.get_managers_admin (cb.from_user.id)
        await cb.message.edit_reply_markup(reply_markup=kb.get_delete_managers_kb(managers))

        try:
            await bot.send_message(del_manager.user_id, 'Ваш статус изменён на "Пользователь"')
        except Exception as ex:
            logging.warning(f'admin 90 {ex}')


# сменить пароль
# @dp.callback_query(text_startswith='edit_password')
@dp.callback_query(lambda cb: cb.data.startswith('edit_password'))
async def edit_password(cb: CallbackQuery, state: FSMContext):
    user = await db.get_admin_info(cb.from_user.id)
    if not user.status:
        await cb.message.answer('❌ У вас нет доступа')
    else:
        await state.set_state('edit_password')
        await state.update_data(data={'status': 'old_pass',
                                      'new_pass': None,
                                      'is_new_admin': None})

        sent = await cb.message.answer('Введите старый пароль', reply_markup=kb.get_cancel_action_button())
        await state.update_data (data={
            'status': 'old_pass',
            'new_pass': None,
            'is_new_admin': None,
            'message_id': sent.message_id
        })


# смена пароля
@dp.message(StateFilter('edit_password'))
async def input_password(msg: Message, state: FSMContext):
    await msg.delete()
    data = await state.get_data()
    if data['status'] == 'old_pass':
        if await db.check_admin_password(user_id=msg.from_user.id, check_password=msg.text):
            text = 'Новый пароль'
            await state.update_data(data={'status': 'new_pass_1'})
            await bot.edit_message_text (
                chat_id=msg.chat.id,
                message_id=data ['message_id'],
                text=text,
                reply_markup=kb.get_cancel_action_button ()
            )
            # await msg.answer(text, reply_markup=kb.get_cancel_action_button())
        else:
            await msg.answer(f'❌ Неверный пароль')

    elif data['status'] == 'new_pass_1':
        text = 'Повторите пароль'
        await state.update_data(data={'status': 'new_pass_2', 'new_pass': msg.text})
        await bot.edit_message_text(
            chat_id=msg.chat.id,
            message_id=data['message_id'],
            text=text,
            reply_markup=kb.get_cancel_action_button ()
        )
        # await msg.answer(text, reply_markup=kb.get_cancel_action_button())

    elif data['status'] == 'new_pass_2':
        if data['new_pass'] == msg.text:
            if data.get('new_admin_id'):
                await db.add_new_admin(
                    id_on_db=data.get('new_admin_id'),
                    user_id=msg.from_user.id,
                    full_name=msg.from_user.full_name,
                    username=msg.from_user.username,
                    password=msg.text
                                       )
            else:
                await db.update_admin_password(user_id=msg.from_user.id, new_password=msg.text)

            await state.clear()
            await msg.answer('✅ Пароль изменён')
            await get_start_admin_screen (msg.chat.id)
        else:
            await msg.answer('❌ Пароли не совпадают')


# передача прав админа
@dp.callback_query(lambda cb: cb.data.startswith('transfer_admin'))
async def transfer_admin(cb: CallbackQuery, state: FSMContext):
    user = await db.get_admin_info (cb.from_user.id)
    if not user.status:
        await cb.message.answer('❌ У вас нет доступа')
    else:
        await state.set_state('transfer_admin')

        text = 'Отправьте username нового администратора\n\n' \
               '❗️Важно:\n' \
               'После отправки username нового администратора ваш статус будет недействителен.\n' \
               'Убедитесь, что вы правильно ввели username нового администратора! В дальнейшем вход в панель ' \
               'администратора будет доступен только с нового аккаунта'

        await cb.message.answer(text, reply_markup=kb.get_cancel_action_button())


# добавляет менеджеров
# @dp.message(state='transfer_admin')
@dp.message(StateFilter('transfer_admin'))
async def new_admin(msg: Message, state: FSMContext):
    await state.clear()
    new_admin_username = msg.text.replace('@', '').strip()
    await db.add_transfer_admin(user_id=msg.from_user.id, new_admin=new_admin_username)
    await msg.answer('✅ Новый администратор назначен')


# добавит пользователя
@dp.callback_query(lambda cb: cb.data.startswith('edit_chat'))
async def admin_change_db(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')

    if action == 'add':
        await state.set_state('add_new_chat')
        text = (f'Вы можете добавить Василия в чат двумя способами:\n\n'
                f'Добавьте пользователя @{UB_USERNAME} в чат и дайте ему статус администратора.\n\n'
                f'Отправьте пригласительную ссылку в чат. Василий сам добавиться в вашу группу, '
                f'но не забудьте дать ему статус администратора.\n\n'
                f'Отправьте пригласительную ссылку')

        sent = await cb.message.answer(text, reply_markup=kb.get_cancel_action_button())
        await state.update_data(data={'message_id': sent.message_id})

    elif action == 'del':
        all_chats = await db.get_all_admin_chats(cb.from_user.id)
        await cb.message.answer('Выберите чат для удаления', reply_markup=kb.get_delete_chats_kb(all_chats))


# принимает ссылку и проверяет её
@dp.message(StateFilter('add_new_chat'))
async def add_new_chat(msg: Message, state: FSMContext):
    await msg.delete()
    if not check_link_in_entities(msg.entities):
        sent = await msg.answer(text='❗️ В сообщении не найдено ссылки')
        await asyncio.sleep(3)
        await sent.delete()

    else:
        chat_info = await add_chat_bot(msg.text)
        if chat_info['error']:
            await msg.answer(chat_info["error_text"])
        else:
            await db.add_new_chat(
                user_id=msg.from_user.id,
                chat_id=chat_info['chat_id'],
                chat_title=chat_info['title'],
                invite_link=None
            )

            await edit_chat_filter(chat_id=chat_info['chat_id'], action='add')
            data = await state.get_data()
            await state.clear()
            await bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=data['message_id'],
                text=f'✅ Чат {chat_info["title"]} добавлен')
            # await msg.answer(f'Чат {chat_info["title"]} добавлен')


# добавит пользователя
@dp.callback_query(lambda cb: cb.data.startswith('delete_chat'))
async def admin_change_db(cb: CallbackQuery, state: FSMContext):
    _, chat_id = cb.data.split(':')
    chat_info = await db.get_chat_info(chat_id)
    await cb.message.edit_text(
        text=f'Подтвердить удаление чата {chat_info.chat_title}',
        reply_markup=kb.get_delete_chats_confirm_kb(chat_id))


# добавит пользователя
@dp.callback_query(lambda cb: cb.data.startswith('confirm_del_chat'))
async def admin_change_db(cb: CallbackQuery, state: FSMContext):
    _, chat_id = cb.data.split(':')
    chat_id = int(chat_id)
    await leave_chat_bot(chat_id)
    await db.delete_chat(chat_id)
    await db.del_tasks_from_chat(chat_id)
    await edit_chat_filter (chat_id=chat_id, action='del')
    await cb.message.edit_text(text='🗑 Чат удалён')
