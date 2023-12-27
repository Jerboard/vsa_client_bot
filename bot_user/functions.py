from bot_user.base import bot

from pyrogram.errors.exceptions import UserAlreadyParticipant, InviteHashExpired

from init import log_error, INVOICE_LINK_NAME


# стартует бот
async def start_bot():
    try:
        await bot.start ()
    except:
        pass


# информация о чате
async def get_chat_info(chat_id: int) -> dict:
    # bot = get_bot_user()
    await start_bot()
    result = await bot.get_chat(chat_id)
    return result


# пробует запросить ссылку
async def get_chat_invite_link(chat_id: int):
    try:
        link_info = await bot.create_chat_invite_link(
            chat_id=chat_id,
            name=INVOICE_LINK_NAME,
            creates_join_request=True
        )
        return link_info.invite_link
    except:
        return 'not_found'


# Добавляется в чат
async def add_chat_bot(invite_link: str) -> dict:
    try:
        await start_bot()
        result = await bot.join_chat(invite_link)
        return {'chat_id': result.id, 'title': result.title, 'error': False}

    except UserAlreadyParticipant as ex:
        return {'error': True, 'error_text': 'Чат уже добавлен'}

    except InviteHashExpired as ex:
        return {'error': True, 'error_text': 'Нерабочая ссылка. Срок действия или лимит пользователей ссылки истёк.\n'
                                             'Проверьте не находиться ли бот в чёрном списке группы'}

    except Exception as ex:
        log_error(ex)
        return {'error': True, 'error_text': 'Не удалось добавить чат. Обратитесь в поддержку'}


# Покидает в чат
async def leave_chat_bot(chat_id: int) -> None:
    try:
        await bot.start()
    except Exception as ex:
        print(ex)
    print(chat_id)
    await bot.leave_chat(chat_id=chat_id)
