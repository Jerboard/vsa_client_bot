from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

import asyncio
from datetime import datetime

import db
from keyboards import inline_kb as kb
from init import dp, TZ, bot, SEND_ERROR_ID
from utils.gpt_utils import chatgpt_response
from utils.async_utils import send_user_tasks
from utils.func import search_deadline, check_tasks_response


# команда старт
@dp.message(Command('start', 'tasks', 'tasks_today'))
async def com_start(msg: Message, state: FSMContext):
    await state.clear()
    if msg.text == '/start':
        # await send_weekly_report()
        is_first = await db.add_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username)

        if is_first:
            await db.update_new_user_tasks(
                user_id=msg.from_user.id,
                fullname=msg.from_user.full_name,
                username=msg.from_user.username)
            text = 'Супер, спасибо за регистрацию! Я теперь доступен в личных сообщениях для помощи и поддержки. ' \
                   'Пиши, если что нужно! 😊'
        else:
            # text = chatgpt_response('Привет!')
            text = 'Привет! Функция помощника пока не доступна'

        await msg.answer(text)

    elif msg.text[:6] == '/tasks':
        user_info = await db.get_user_info(msg.from_user.id)
        await send_user_tasks(msg.from_user.id, msg.chat.id, user_info.status)
        if msg.text == '/tasks_today':
            today = datetime.now(TZ).date()
            await send_user_tasks(msg.from_user.id, msg.chat.id, user_info.status, period=today)

    else:
        await db.add_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username)
        user_info = await db.get_user_info(msg.from_user.id)
        command = msg.text.split(' ')[1] if len(msg.text.split(' ')) > 1 else None
        if command[:10] == 'tasks_chat':
            chat_id = command[10:]
            await send_user_tasks(user_id=msg.from_user.id,
                                  chat_id=chat_id,
                                  status=user_info.status)

        # elif command == 'report_3':
        #     target_date = datetime.now(TZ).date() + timedelta(days=3)
        #     await send_user_tasks(user_id=msg.from_user.id,
        #                           chat_id=msg.chat.id,
        #                           status=user_info.status,
        #                           period=target_date)

        # elif command == 'report_week':
        #     top_statistic_text = await db.get_top_users_text(True)
        #     statistic_text = f'*Лучшие на неделе:*\n\n' \
        #                      f'{top_statistic_text}'
        #
        #     target_date = datetime.now(TZ).date() + timedelta(days=6)
        #     await send_user_tasks(user_id=msg.from_user.id,
        #                           chat_id=msg.chat.id,
        #                           status=user_info.status,
        #                           period=target_date)
        #
        #     await msg.answer(statistic_text, parse_mode='markdown')


# команда админ
@dp.message(Command('admin'))
async def com_admin(msg: Message, state: FSMContext):
    await state.clear()
    admin_info = await db.get_admin_info (msg.from_user.id, msg.from_user.username)
    if admin_info:
        if admin_info.status == 'new':
            await state.set_state ('edit_password')
            sent = await msg.answer ('Придумайте пароль администратора', reply_markup=kb.get_cancel_action_button ())
            await state.update_data (data={
                'status': 'new_pass_1',
                'new_pass': None,
                'new_admin_id': admin_info.id,
                'message_id': sent.message_id})

        else:
            await state.set_state ('input_password')
            await state.update_data (data={'try': 3})
            await msg.answer ('Введите пароль администратора')

    else:
        await msg.answer ('❌ У вас нет доступа')


# закрыть задачу
@dp.callback_query(lambda cb: cb.data.startswith('close_task'))
async def close_task(cb: CallbackQuery):
    _, action, task_id = cb.data.split(':')

    message_head = cb.message.text.split('\n\n')[0]
    message_text = cb.message.text[len(message_head):]

    if action == 'done':
        await db.make_task_done(task_id)
        await cb.message.edit_text(f'✅ Выполнено{message_text}')

    elif action == 'cancel':
        await db.update_task_status(task_id, status='cancel')
        await cb.message.edit_text(f'🗑 Удалена{message_text}')

    elif action == 'error':
        await db.update_task_status(task_id, status='error')
        await cb.message.delete()
        await cb.answer('❗️ Отчёт отправлен разработчикам. Спасибо за сообщение')
        await bot.send_message(SEND_ERROR_ID, f'❌ Ошибка{message_text}')


# контекст задачи
@dp.callback_query(lambda cb: cb.data.startswith('context'))
async def close_task(cb: CallbackQuery):
    _, chat_id, message_id = cb.data.split (':')

    messages = await db.get_context_message(chat_id, message_id)

    for message in messages:
        try:
            text = f'<b>{message.sender_full_name}</b>\n\n' \
                   f'{message.text}'

            await bot.send_message(chat_id=cb.message.chat.id, text=text)

        except Exception as ex:
            print(ex)


# перенос дедлайна
@dp.callback_query(lambda cb: cb.data.startswith('edit_deadline'))
async def edit_deadline(cb: CallbackQuery, state: FSMContext):
    _, task_id = cb.data.split(':')
    # await UserStats.new_deadline.set()
    await state.set_state('new_deadline')
    await state.update_data(data={'task_id': task_id, 'message_id': cb.message.message_id})
    await cb.message.answer('Да, давай перенесём! Когда новый срок?', reply_markup=kb.get_cancel_action_button())


# новый дедлайн
@dp.message(StateFilter('new_deadline'))
async def new_deadline(msg: Message, state: FSMContext):
    deadline = search_deadline(msg.text)
    if deadline is None:
        await msg.answer('Не понял тебя( Можешь написать чуть подробнее?',
                         reply_markup=kb.get_cancel_action_button())
    else:
        data = await state.get_data()
        await state.clear()
        await db.edit_deadline(data['task_id'], deadline)
        deadline_string = deadline.strftime('%d.%m.%y %H:%M')

        text = f'Поменял. Новый дедлайн: {deadline_string}'
        await bot.send_message(msg.chat.id, text, reply_to_message_id=data['message_id'])


# перенос дедлайна
@dp.callback_query(lambda cb: cb.data.startswith('cancel_action'))
async def cancel_action(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.delete()
    sent = await cb.message.answer('Ок, вернул всё как было')
    await asyncio.sleep(4)
    await sent.delete()


@dp.message(StateFilter(default_state))
async def take_messages(msg: Message, state: FSMContext):
    # определяет запрос задач для чата, выводит их в личку
    if check_tasks_response(msg.text):
        user_info = await db.get_user_info(msg.from_user.id)
        period = search_deadline(msg.text)
        period = period.date() if period is not None else None
        await send_user_tasks(msg.from_user.id, msg.chat.id, user_info.status, period)

    else:
        # gpt_answer = chatgpt_response(msg.text)
        # await msg.reply(gpt_answer)
        await msg.answer('Привет! Функция помощника пока не доступна')
