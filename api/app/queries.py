from typing import Optional

import asyncpg


class NotEnoughMoneyError(Exception):
    """Ошибка, возникающая, если у клиента недостаточно денег."""


async def query_add(
    connection: asyncpg.Connection, uuid: str, how_much: int
) -> Optional[asyncpg.Record]:
    """Запрос для пополнения счёта клинта.

    :param connection: соединение
    :param uuid: идентификатор клиента
    :param how_much: количество копеек, которые нужно прибавить на баланс клиента
    """
    async with connection.transaction():
        row = await connection.fetchrow(
            """
            UPDATE
                client
            SET
                balance = balance + GREATEST(0, $2)
            WHERE
                id = $1 AND
                is_open = TRUE
            RETURNING *
            """,
            uuid,
            how_much,
        )
        return row


async def query_subtract(
    connection: asyncpg.Connection, uuid: str, how_much: int
) -> Optional[asyncpg.Record]:
    """Запрос на снятие указанной суммы со счёта клиента.

    :param connection: соединение
    :param uuid: идентификатор клиента
    :param how_much: количество копеек, которые нужно снять с баланса клиента
    :raises NotEnoughMoneyError: если на счёте клиента недостаточно денег
    """
    async with connection.transaction():
        row: Optional[asyncpg.Record] = await connection.fetchrow(
            """
            UPDATE
                client
            SET
                hold = hold + GREATEST(0, $2)
            WHERE
                id = $1 AND
                is_open = TRUE
            RETURNING *
            """,
            uuid,
            how_much,
        )
        if row is not None and row["balance"] - row["hold"] < 0:
            raise NotEnoughMoneyError
        return row


async def query_status(
    connection: asyncpg.Connection, uuid: str
) -> Optional[asyncpg.Record]:
    """Запрос для получения текущего состояния счёта клиента.

    :param connection: соединение
    :param uuid: идентификатор клиента
    """
    row: Optional[asyncpg.Record] = await connection.fetchrow(
        """
        SELECT * FROM client WHERE id = $1
        """,
        uuid,
    )
    return row


async def query_unhold_all(connection: asyncpg.Connection) -> None:
    """Запрос для обновления баланса и обнуления холда у всех клиентов.

    :param connection: соединение
    """
    async with connection.transaction():
        await connection.execute(
            """
            UPDATE
                client
            SET
                balance = balance - hold,
                hold = 0
            """
        )
