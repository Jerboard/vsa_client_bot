import sqlalchemy as sa
import typing as t

from db.base import METADATA, begin_connection


class UserRow(t.Protocol):
    id: int
    user_id: str
    full_name: str
    username: str
    status: str


UsersTable = sa.Table(
    'users',
    METADATA,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('user_id', sa.String(50)),
    sa.Column('full_name', sa.String(128)),
    sa.Column('username', sa.String(32)),
    sa.Column('status', sa.String(50), default='user'),
    sa.Column('admin_id', sa.Integer),
)


# проверка на первое посещение
async def add_user(user_id: int, full_name: str, username: str) -> bool:
    async with begin_connection () as conn:
        result = await conn.execute(UsersTable.select().where(UsersTable.c.user_id == user_id))

        user = result.first ()
        if user:
            return False
        else:
            result = await conn.execute (UsersTable.select ().where (UsersTable.c.username == username))
            user = result.first ()
            if user:
                payloads = dict(user_id=user_id, full_name=full_name)
                await conn.execute(UsersTable.update().where(UsersTable.c.user_id == username).values(payloads))
            else:
                payloads = dict (user_id=user_id, full_name=full_name, username=username)
                await conn.execute (UsersTable.insert ().values (payloads))

            return True


# возвращает ИД по юзернейму
async def get_user_info(user_id: t.Union[str, int]) -> UserRow:
    if type(user_id) == int:
        query = UsersTable.select().where(UsersTable.c.user_id == user_id)
    else:
        query = UsersTable.select ().where (UsersTable.c.username == user_id)
    async with begin_connection () as conn:
        result = await conn.execute(query)
    return result.first()


# добавляет менеджера
async def add_new_manager(username: str) -> t.Union[str, None]:
    async with begin_connection () as conn:
        result = await conn.execute(UsersTable.select().where(UsersTable.c.username == username))
        manager = result.first()
        # manager = UserRow (row) if row else None

        if manager:
            await conn.execute(
                UsersTable.update ().where (UsersTable.c.user_id == manager.user_id).values (status='manager')
            )
            return manager.user_id

        else:
            await conn.execute(UsersTable.insert().values(username=username, status='manager'))
            return None


# список менеджеров
async def get_managers_admin(user_id: int) -> tuple[UserRow]:
    async with begin_connection () as conn:
        result = await conn.execute(
            UsersTable.select().where(sa.and_(UsersTable.c.status == 'manager',
                                              UsersTable.c.admin_id == user_id)))

    return result.all()


# лишает статуса менеджера
async def delete_manager_status(id_user_table: str) -> UserRow:
    async with begin_connection () as conn:
        manager = await conn.execute(UsersTable.select().where(UsersTable.c.id == id_user_table))
        await conn.execute(UsersTable.update().where(UsersTable.c.id == id_user_table).values(status='user',
                                                                                              admin_id=None))
    return manager.first()


# даёт статуса менеджера связка с инфо
async def take_manager_status(username: str) -> None:
    async with begin_connection () as conn:
        result = await conn.execute(UsersTable.select().where(UsersTable.c.username == username))
        admin = result.first()
        if admin:
            await conn.execute (UsersTable.update ().where (UsersTable.c.username == username).values (status='admin'))
        else:
            await conn.execute (UsersTable.insert ().values (username=username, status='admin'))
