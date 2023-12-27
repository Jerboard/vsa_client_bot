import sqlalchemy as sa
import typing as t

from datetime import datetime

from db.base import METADATA, begin_connection
from init import TZ


class MessageHistoryRow(t.Protocol):
    id: int
    sent_time: datetime
    chat_id: str
    message_id: str
    sender_id: str
    sender_full_name: str
    sender_username: str
    text: str


MessageHistoryTable = sa.Table(
    'message_history',
    METADATA,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('sent_time', sa.DateTime(timezone=True)),
    sa.Column('chat_id', sa.String(50)),
    sa.Column('message_id', sa.String(50)),
    sa.Column('sender_id', sa.String(50)),
    sa.Column('sender_full_name', sa.String(64)),
    sa.Column('sender_username', sa.String(50)),
    sa.Column('text', sa.Text)
)


# отправляет контекст сообщения
async def get_context_message(chat_id: str, message_id: str):
    start_message_id = int(message_id) - 2
    end_message_id = int(message_id) + 3
    async with begin_connection () as conn:
        result = await conn.execute(MessageHistoryTable.select().where(
            sa.and_(
                MessageHistoryTable.c.chat_id == chat_id,
                MessageHistoryTable.c.message_id >= start_message_id,
                MessageHistoryTable.c.message_id <= end_message_id,
                )
            )
        )

    return result.all()


# удаляет все сообщения старше даты
async def old_message_delete(target_date: datetime) -> None:
    async with begin_connection () as conn:
        await conn.execute(MessageHistoryTable.delete().where(MessageHistoryTable.c.sent_time < target_date))
