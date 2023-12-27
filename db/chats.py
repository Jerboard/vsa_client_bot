import sqlalchemy as sa
import typing as t

from datetime import date, datetime

from init import TZ
from db.base import METADATA, begin_connection


class ChatRow(t.Protocol):
    id: int
    owner_id: int
    chat_id: int
    chat_title: str
    invite_link: str
    added_at: date
    status: str


ChatTable = sa.Table(
    'chats',
    METADATA,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('owner_id', sa.BigInteger),
    sa.Column('chat_id', sa.BigInteger),
    sa.Column('chat_title', sa.String(255)),
    sa.Column('invite_link', sa.String(255)),
    sa.Column('added_at', sa.Date),
)


# сохраняет пароль администратора
async def add_new_chat(user_id: int, chat_id: int, chat_title: str, invite_link: t.Optional[str]) -> None:
    today = datetime.now(TZ).date()
    query = ChatTable.insert().values(
        owner_id=user_id,
        chat_id=chat_id,
        chat_title=chat_title,
        added_at=today)
    async with begin_connection() as conn:
        await conn.execute(query)


# возвращает инфо по чату
async def get_chat_info(chat_id: t.Union[str, int]) -> t.Union[ChatRow, None]:
    query = ChatTable.select().where(ChatTable.c.chat_id == chat_id)
    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.first()


# все чаты пользователя
async def get_all_admin_chats(user_id: int) -> tuple[ChatRow]:
    query = ChatTable.select().where(ChatTable.c.owner_id == user_id)
    async with begin_connection() as conn:
        result = await conn.execute(query)
    return result.all()


# удалить чат
async def delete_chat(chat_id: t.Union[str, int]) -> None:
    query = ChatTable.delete().where(ChatTable.c.chat_id == chat_id)
    async with begin_connection() as conn:
        await conn.execute(query)
