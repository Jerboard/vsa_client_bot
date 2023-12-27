import typing as t

from datetime import datetime, timedelta, date

import db
from init import TZ, bot, START_LINK, DATETIME_STR_FORMAT, log_error
from keyboards.inline_kb import get_task_kb
from utils.func import create_rating_text


# отправляет список задач
async def send_user_tasks(user_id: int, chat_id: t.Union[int, None], status: str, period: date = None) -> None:
    time_start = datetime.now()
    if user_id == chat_id:
        chat_id = None

    tasks = await db.get_tasks_user(
        user_id=user_id,
        chat_id=chat_id,
        status=status,
        period=period)

    if not tasks:
        if chat_id:
            chat = await db.get_chat_info(chat_id)
            text = f'У вас нет текущих задач в чате {chat.chat_title}'
        else:
            text = 'У вас нет текущих задач'
        await bot.send_message(user_id, text)

    else:
        for task in tasks:
            priority_flag = '' if task.is_priority is False else '‼️'

            now = datetime.now(TZ)
            if TZ.localize(task.deadline) < now:
                priority_flag = priority_flag + ' ⏰'
                text = f'<b>{task.task_text}</b>'
            else:
                text = task.task_text

            deadline_string = task.deadline.strftime(DATETIME_STR_FORMAT)
            time_add = task.create_time.strftime(DATETIME_STR_FORMAT)

            if task.invite_link:
                chat_name = f'<a href="{task.invite_link}">{task.chat_title}</a>'
            else:
                chat_name = task.chat_title

            if status == 'user':
                text = f'{priority_flag}\n' \
                       f'<b>Чат:</b> {chat_name}\n' \
                       f'<b>Поставлена:</b> {time_add}\n' \
                       f'<b>Дедлайн:</b> {deadline_string}\n\n' \
                       f'{text}'
            else:

                text = f'{priority_flag}\n' \
                       f'<b>Чат:</b> {chat_name}\n' \
                       f'<b>Поставлена:</b> {time_add}\n' \
                       f'<b>Дедлайн:</b> {deadline_string}\n' \
                       f'<b>Ответственный:</b> @{task.assigned_username}\n\n' \
                       f'{text}'

            try:
                if str(user_id).isdigit():
                    await bot.send_message(chat_id=user_id,
                                           text=text,
                                           disable_web_page_preview=True,
                                           reply_markup=get_task_kb(task.id, task.chat_id, task.message_id))
                else:
                    log_error(f'dont send message on user {user_id}')

            except Exception as ex:
                log_error(ex)

    speed = datetime.now() - time_start
    await db.add_action(
        action_name='Просмотр задач',
        comment=str(len(tasks)),
        speed=speed.seconds
    )


# задачи на 3 дня вперёд каждый день в час дня
async def send_tasks_on_next_3_days():
    time_start = datetime.now ()
    target_date = datetime.now(TZ).date() + timedelta(days=3)
    users_ids = await db.get_have_tasks_on_period(target_date, status='user')

    for user_id in users_ids:
        if user_id.isdigit():
            await send_user_tasks(user_id=user_id,
                                  chat_id=None,
                                  status='user',
                                  period=target_date)

        else:
            chats_ids = await db.get_assigned_chats(user_id)
            text = f'@{user_id}, чтобы получить список задач на ближайшие три дня перейдите по ссылке ' \
                   f'{START_LINK}report_3 и нажмите "Старт" в нижней части экрана'

            for chat_id in chats_ids:
                await bot.send_message(chat_id, text)

    speed = datetime.now () - time_start
    await db.add_action (
        action_name='Задачи на 3 дня',
        comment=f'Для {len(users_ids)} пользователей',
        speed=speed.seconds
    )


# задачи для менеджеров на завтра в 17:00
async def send_tasks_tomorrow_for_managers():
    time_start = datetime.now ()
    tomorrow = datetime.now(TZ).date() + timedelta(days=1)
    managers = await db.get_have_tasks_on_period(tomorrow, status='manager')
    for manager_id in managers:
        await send_user_tasks(user_id=manager_id,
                              chat_id=None,
                              status='manager',
                              period=tomorrow)

    speed = datetime.now () - time_start
    await db.add_action (
        action_name='Задачи на завтра для менеджеров',
        comment=f'Для {len(managers)} пользователей',
        speed=speed.seconds
    )


# недельный отчёт
async def send_weekly_report():
    time_start = datetime.now ()
    active_admins = await db.get_all_admins_info(status='active')

    sunday = datetime.now(TZ).date() + timedelta(days=6)
    last_monday = datetime.now(TZ).date() - timedelta(days=7)
    last_sunday = datetime.now(TZ).date() - timedelta(days=1)

    for admin in active_admins:
        all_admin_tasks_on_week = await db.get_tasks_user(
            user_id=admin.user_id,
            chat_id=None,
            status='admin',
            period=sunday
        )
        users_have_tasks_on_week = set(user_row.assigned for user_row in all_admin_tasks_on_week)

        for user_id in users_have_tasks_on_week:
            if user_id:
                await bot.send_message (user_id, '<b>Ваши задачи на неделю:</b>')
                await send_user_tasks(
                    user_id=user_id,
                    chat_id=None,
                    status='user',
                    period=sunday
                )

        all_admin_tasks_last_week = await db.get_all_user_with_task_for_rating(
            owner_id=admin.user_id,
            start_date=last_monday,
            end_date=last_sunday
        )
        text = create_rating_text(all_admin_tasks_last_week)
        statistic_text = f'<b>Лучшие на неделе:</b>\n\n{text}'
        # print(statistic_text)

        users_have_tasks_on_last_week = set (user_row.assigned for user_row in all_admin_tasks_last_week)

        for user_id in users_have_tasks_on_last_week:
            if user_id:
                print(user_id)
                await bot.send_message(
                    chat_id=user_id,
                    text=statistic_text
                )

    speed = datetime.now () - time_start
    await db.add_action (
        action_name='Недельный отчёт',
        comment=f'-',
        speed=speed.seconds
    )


# месячный отчёт
async def send_monthly_report():
    time_start = datetime.now ()
    all_users = await db.get_all_assigned()
    top_statistic_text = await db.get_top_users_text()
    top_count_tasks_text = await db.get_top_users_text_tasks()

    statistic_text = f'<b>Самые быстрые в месяце:</b>\n\n' \
                     f'{top_statistic_text}'
    statistic_count_text = f'<b>Больше всего задач:</b>\n\n' \
                           f'{top_count_tasks_text}'

    for user_id in all_users:
        if user_id.isdigit():

            await bot.send_message(user_id, statistic_text)
            await bot.send_message(user_id, statistic_count_text)

    speed = datetime.now () - time_start
    await db.add_action (
        action_name='Месячный отчёт',
        comment=f'-',
        speed=speed.seconds
    )