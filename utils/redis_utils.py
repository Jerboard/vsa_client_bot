import json

import db
from init import redis_client, FILTER_CHAT_DATA_NAME


# создаёт фильтр чатов при запуске
async def create_filter_active_chats():
    work_chats_raw = await db.get_all_active_chats()
    work_chats = [chat[0] for chat in work_chats_raw]
    redis_client.set (FILTER_CHAT_DATA_NAME, json.dumps (work_chats))


# добавляет чат в фильтр
async def edit_chat_filter(chat_id: int, action: str) -> None:
    stored_data = redis_client.get (FILTER_CHAT_DATA_NAME)
    chats: list[int] = json.loads (stored_data)
    if action == 'add':
        chats.append(chat_id)
    elif action == 'del':
        chats.remove(chat_id)
    redis_client.set (FILTER_CHAT_DATA_NAME, json.dumps (chats))
