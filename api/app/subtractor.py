import asyncio
import logging

import asyncpg

from .settings import Settings

logging.basicConfig(level=logging.INFO)


async def subtract(connection: asyncpg.Connection) -> None:
    logging.info("Subtracting holds from balances...")
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


async def periodic_subtract() -> None:
    logging.info("Starting...")
    settings = Settings()
    connection = await asyncpg.connect(dsn=settings.pg_dsn)
    while True:
        await asyncio.sleep(settings.subtract_interval)
        await subtract(connection)
