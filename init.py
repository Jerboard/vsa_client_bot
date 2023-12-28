from aiogram import Dispatcher
from aiogram.types.bot_command import BotCommand
from aiogram import Bot
from aiogram.enums import ParseMode

from pyrogram import Client
from datetime import datetime

import traceback
import logging
import redis

from dotenv import load_dotenv
from os import getenv
from pytz import timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

import asyncio
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

load_dotenv ()
loop = asyncio.get_event_loop()
dp = Dispatcher()
bot = Bot(getenv("TOKEN"), parse_mode=ParseMode.HTML)

bot_user = Client("zhenia_test")

TZ = timezone('Europe/Moscow')
FILTER_CHAT_DATA_NAME = getenv('FILTER_CHAT_DATA_NAME')
START_LINK = getenv ('START_LINK')

DATETIME_STR_FORMAT = '%d.%m.%y %H:%M'

scheduler = AsyncIOScheduler(timezone=TZ)

ENGINE = create_async_engine(url=getenv('DB_URL_TEST'))
redis_client = redis.StrictRedis(host=getenv('REDIS_HOST'), port=getenv('REDIS_PORT'), db=0)

SEND_ERROR_ID = getenv('SEND_ERROR_ID')
INVOICE_LINK_NAME = getenv('INVOICE_LINK_NAME')
UB_USERNAME = getenv('UB_USERNAME')

API_UB_ID = getenv('API_ID')
API_UB_HAS = getenv('API_HAS')


async def set_main_menu() -> None:
    main_menu_commands = [
        BotCommand (command='/start',
                    description='Перезапуск'),
        BotCommand(command='/tasks',
                   description='Мои задачи'),
        BotCommand (command='/tasks_today',
                    description='Задачи на сегодня'),
        BotCommand (command='/admin',
                    description='Панель администратора')
    ]

    await bot.set_my_commands(main_menu_commands)


def log_error(message):
    timestamp = datetime.now(TZ)
    filename = traceback.format_exc()[1]
    line_number = traceback.format_exc()[2]
    logging.error(f'{timestamp} {filename} {line_number}: {message}')