import sqlalchemy as sa
import typing as t
import bcrypt

from datetime import date

from db.base import METADATA, begin_connection
from db.chats import ChatTable


class AdminRow(t.Protocol):
    id: int
    user_id: int
    full_name: str
    username: str
    password: str
    transfer_admin: str
    status: str
    end_date: date


AdminTable = sa.Table(
    'admins',
    METADATA,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('user_id', sa.Integer),
    sa.Column('full_name', sa.String(255)),
    sa.Column('username', sa.String(255)),
    sa.Column('password', sa.String(255)),
    sa.Column('transfer_admin', sa.String(50)),
    sa.Column('status', sa.String(50), default='new'),
    sa.Column('end_date', sa.Date),
)


# сохраняет пароль администратора
async def update_admin_password(user_id: int, new_password: str) -> None:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
    async with begin_connection () as conn:
        await conn.execute (AdminTable.update().where(AdminTable.c.user_id == user_id).values(password=hashed_password))


# инфо
async def get_admin_info(user_id: int, username: str = None) -> AdminRow:
    if username:
        query = AdminTable.select().where(sa.or_(AdminTable.c.user_id == user_id, AdminTable.c.username == username))
    else:
        query = AdminTable.select().where(AdminTable.c.user_id == user_id)
    async with begin_connection () as conn:
        result = await conn.execute (query)
    return result.first()


# сохраняет пароль администратора
async def check_admin_password(user_id: int, check_password: str) -> bool:
    info = await get_admin_info(user_id)
    hashed_password = info.password.encode('utf-8')  # Кодируем байтовую строку
    return bcrypt.checkpw(check_password.encode('utf-8'), hashed_password)


# добавляет юзернейм нового админа
async def add_transfer_admin(user_id: int, new_admin: str) -> None:
    async with begin_connection () as conn:
        await conn.execute(AdminTable.update().where(AdminTable.c.user_id == user_id).values(
            transfer_admin=new_admin,
            status='transfer'))


# вводит нового администратора
async def add_new_admin(id_on_db: int, user_id: int, full_name: str, username: str, password: str) -> None:
    salt = bcrypt.gensalt ()
    hashed_password = bcrypt.hashpw (password.encode ('utf-8'), salt)

    query = AdminTable.update().where(AdminTable.c.id == id_on_db).values(
            user_id=user_id,
            full_name=full_name,
            username=username,
            password=hashed_password,
            status='active')

    async with begin_connection () as conn:
        await conn.execute(query)


# все админы со статусом (актив по умолчанию)
async def get_all_admins_info(status: str = None) -> tuple[AdminRow]:
    query = AdminTable.select()

    if status:
        query = query.where(AdminTable.c.status == status)

    async with begin_connection () as conn:
        result = await conn.execute (query)
    return result.all()