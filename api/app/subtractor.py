import asyncio
import logging

import asyncpg

from app.settings import Settings
from app.queries import query_unhold_all

logging.basicConfig(level=logging.INFO)


async def periodic_subtract() -> None:
    logging.info("Starting...")
    settings = Settings()
    connection = await asyncpg.connect(dsn=settings.pg_dsn)
    while True:
        await asyncio.sleep(settings.subtract_interval)
        logging.info("Subtracting holds from balances...")
        await query_unhold_all(connection)
