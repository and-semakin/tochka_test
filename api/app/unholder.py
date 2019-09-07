import asyncio
import logging

import asyncpg

from app.settings import Settings
from app.queries import query_unhold_all


async def periodic_unhold_all() -> None:
    """Обнулять холд и обновлять баланс клиентов каждые `unhold_all_interval` секунд."""
    logging.info("Starting...")
    settings = Settings()
    connection = await asyncpg.connect(dsn=settings.pg_dsn)
    while True:
        await asyncio.sleep(settings.unhold_all_interval)
        logging.info("Subtracting holds from balances...")
        await query_unhold_all(connection)
