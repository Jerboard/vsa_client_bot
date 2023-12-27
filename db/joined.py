import sqlalchemy as sa
import typing as t

from datetime import datetime, date, timedelta

from init import TZ, log_error
from db.base import METADATA, begin_connection
from utils.func import get_delay_string

from db.users import UsersTable, UserRow
from db.admins import AdminTable, AdminRow
from db.chats import ChatTable, ChatRow
from db.message_history import MessageHistoryTable, MessageHistoryRow
from db.tasks import TasksTable, TaskRow


class ChatAdminRow(t.Protocol):
    id_admin_table: int
    admin_user_id: int
    admin_full_name: str
    admin_username: str
    status: str
    end_date: date
    chat_id: int
    title: str
    invite_link: str
    added_at: date


class ChatTaskRow(t.Protocol):
    id: int
    owner_id: int
    chat_id: int
    invite_link: str
    added_at: date
    create_time: datetime
    message_id: int
    chat_title: str
    manager: str
    assigned: int
    assigned_username: str
    deadline: datetime
    task_text: str
    delay: int
    is_priority: bool


# Все активные чаты для фильтра
async def get_all_active_chats() -> list[tuple[int]]:
    query = (
        sa.select (
            ChatTable.c.chat_id.label ('chat_id'),
        )
        .select_from (AdminTable.join (ChatTable, AdminTable.c.user_id == ChatTable.c.owner_id))
    ).where(AdminTable.c.status != 'inactive')

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.all()


async def get_tasks_user(
        user_id: int,
        chat_id: t.Optional [int],
        status: str,
        period: date) -> tuple [ChatTaskRow]:

    query = sa.select(
        TasksTable.c.id,
        TasksTable.c.create_time,
        TasksTable.c.message_id,
        TasksTable.c.chat_title,
        TasksTable.c.manager,
        TasksTable.c.assigned,
        TasksTable.c.assigned_username,
        TasksTable.c.deadline,
        TasksTable.c.task_text,
        TasksTable.c.delay,
        TasksTable.c.is_priority,
        ChatTable.c.owner_id,
        ChatTable.c.chat_id,
        ChatTable.c.invite_link,
        ChatTable.c.added_at,
    ).join (ChatTable, TasksTable.c.chat_id == ChatTable.c.chat_id).where (TasksTable.c.status == 'active').order_by (
        TasksTable.c.is_priority,
        TasksTable.c.chat_id,
        TasksTable.c.deadline.desc ())

    # query = (TasksTable.join (ChatTable, TasksTable.c.chat_id == ChatTable.c.chat_id).select().
    #          where (TasksTable.c.status == 'active').order_by (
    #     TasksTable.c.is_priority,
    #     TasksTable.c.chat_id,
    #     TasksTable.c.deadline.desc ()
    # ))

    if status == 'user':
        query = query.where(TasksTable.c.assigned == user_id)

    elif status == 'admin':
        query = query.where (ChatTable.c.owner_id == user_id)

    else:
        query = query.where (TasksTable.c.manager == user_id)

    if chat_id:
        query = query.where(TasksTable.c.chat_id == chat_id)

    if period:
        query = query.where (TasksTable.c.deadline <= period)

    now = datetime.now(TZ)

    delay_query = query.where (TasksTable.c.deadline > now)
    current_query = query.where (TasksTable.c.deadline <= now)

    async with begin_connection () as conn:
        delay_result = await conn.execute(delay_query)
        current_result = await conn.execute(current_query)

    all_tasks = delay_result.all() + current_result.all()
    return all_tasks


# список пользователей имеющих задачи за период
async def get_all_user_with_task_for_rating(
        owner_id: int,
        start_date: date = None,
        end_date: date = None) -> tuple[TaskRow]:

    query = (TasksTable.join (ChatTable, TasksTable.c.chat_id == ChatTable.c.chat_id).select().with_only_columns(
        TasksTable.c.assigned,
        TasksTable.c.assigned_username,
        sa.func.sum(TasksTable.c.delay).label('delay'),
        sa.func.count(TasksTable.c.id).label('all_tasks')
    ).where(ChatTable.c.owner_id == owner_id, TasksTable.c.status == 'done')).group_by(
        TasksTable.c.assigned_username,
        TasksTable.c.assigned)

    if start_date:
        query = query.where(TasksTable.c.deadline >= start_date)

    if end_date:
        query = query.where(TasksTable.c.deadline <= end_date)

    async with begin_connection () as conn:
        result = await conn.execute(query)

    return result.all()