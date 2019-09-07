import asyncio
import functools
from typing import Callable, Any

import asyncpg
import pytest

from app.main import init_connection
from app.queries import (
    query_status,
    query_add,
    query_subtract,
    query_unhold_all,
    NotEnoughMoneyError,
)
from app.settings import Settings


def run_until_complete(function: Callable) -> Callable:
    """Декоратор, выполняющий функцию в евентлупе."""

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.get_event_loop().run_until_complete(function(*args, **kwargs))

    return wrapper


@pytest.mark.asyncio
class TestServerQueries:
    """Тесты для запросов к БД, которые выполняются из API."""

    settings = Settings()

    @classmethod
    @run_until_complete
    async def setup_class(cls) -> None:
        """До начала тестов копируем базу."""
        connection = await asyncpg.connect(dsn=cls.settings.pg_dsn)
        try:
            await connection.execute(
                f"DROP DATABASE IF EXISTS {cls.settings.postgres_test_db}"
            )
            await connection.execute(
                """
                SELECT
                    pg_terminate_backend(pg_stat_activity.pid)
                FROM
                    pg_stat_activity
                WHERE
                    pg_stat_activity.datname = $1 AND
                    pid <> pg_backend_pid();
                """,
                cls.settings.postgres_db,
            )
            await connection.execute(
                f"""
                CREATE DATABASE {cls.settings.postgres_test_db}
                WITH TEMPLATE {cls.settings.postgres_db}
                """
            )
        finally:
            await connection.close()

    @pytest.fixture()
    async def connection(self) -> asyncpg.Connection:
        """Фикстура, возвращающая соединение к тестовой базе данных."""
        connection = await asyncpg.connect(dsn=self.settings.pg_test_dsn)
        try:
            await init_connection(connection)
            yield connection
        finally:
            await connection.close()

    @pytest.fixture()
    async def test_data(self, connection) -> None:
        """Очистить таблицу `client` и наполнить её заново тестовыми данными."""
        await connection.execute("TRUNCATE client")
        await connection.execute(
            """
            INSERT INTO client
                   (id, name, balance, hold, is_open)
            VALUES
                   (
                          '26c940a1-7228-4ea2-a3bc-e6460b172040',
                          'Петров Иван Сергеевич',
                          1700,
                          300,
                          TRUE
                   ),
                   (
                          '7badc8f8-65bc-449a-8cde-855234ac63e1',
                          'Kazitsky Jason',
                          200,
                          200,
                          TRUE
                   ),
                   (
                          '5597cc3d-c948-48a0-b711-393edf20d9c0',
                          'Пархоменко Антон Александрович',
                          10,
                          300,
                          TRUE
                   ),
                   (
                          '867f0924-a917-4711-939b-90b179a96392',
                          'Петечкин Петр Измаилович',
                          1000000,
                          1,
                          FALSE
                   );
            """
        )

    async def test_status(self, test_data, connection: asyncpg.Connection) -> None:
        """Проверить запрос получения статуса.

        :param test_data: добавить тестовые данные в таблицу
        :param connection: соединение к базе
        """
        not_existing_client_status = await query_status(
            connection, "00000000-0000-0000-0000-000000000000"
        )
        assert not_existing_client_status is None

        client_status = await query_status(
            connection, "26c940a1-7228-4ea2-a3bc-e6460b172040"
        )
        assert client_status["id"] == "26c940a1-7228-4ea2-a3bc-e6460b172040"
        assert client_status["name"] == "Петров Иван Сергеевич"
        assert client_status["balance"] == 1700
        assert client_status["hold"] == 300
        assert client_status["is_open"] is True

    async def test_add(self, test_data, connection: asyncpg.Connection) -> None:
        """Проверить запрос пополнения счёта клиента.

        :param test_data: добавить тестовые данные в таблицу
        :param connection: соединение к базе
        """
        # пополнение несуществующего счёта возвращает None
        client_status = await query_add(
            connection, "00000000-0000-0000-0000-000000000000", 1000
        )
        assert client_status is None

        # запрос с пополнением на 0 не изменяет ничего
        client_status = await query_add(
            connection, "26c940a1-7228-4ea2-a3bc-e6460b172040", 0
        )
        assert client_status["id"] == "26c940a1-7228-4ea2-a3bc-e6460b172040"
        assert client_status["name"] == "Петров Иван Сергеевич"
        assert client_status["balance"] == 1700
        assert client_status["hold"] == 300
        assert client_status["is_open"] is True

        # запрос с пополнением на отрицательное число денег тоже не изменяет ничего
        client_status = await query_add(
            connection, "26c940a1-7228-4ea2-a3bc-e6460b172040", -1000
        )
        assert client_status["balance"] == 1700
        assert client_status["hold"] == 300

        # успешный запрос
        client_status = await query_add(
            connection, "26c940a1-7228-4ea2-a3bc-e6460b172040", 1000
        )
        assert client_status["balance"] == 2700
        assert client_status["hold"] == 300

        # пополнение закрытого счёта возвращает None
        client_status = await query_add(
            connection, "867f0924-a917-4711-939b-90b179a96392", 1000
        )
        assert client_status is None
        # баланс счёта не изменился
        client_status = await query_status(
            connection, "867f0924-a917-4711-939b-90b179a96392"
        )
        assert client_status["balance"] == 1_000_000

    async def test_subtract(self, test_data, connection: asyncpg.Connection) -> None:
        """Проверить запрос снятие денег со счёта клиента.

        :param test_data: добавить тестовые данные в таблицу
        :param connection: соединение к базе
        """
        # снятие денег с несуществующего счёта возвращает None
        client_status = await query_subtract(
            connection, "00000000-0000-0000-0000-000000000000", 1000
        )
        assert client_status is None

        # запрос со снятием на 0 не изменяет ничего
        client_status = await query_subtract(
            connection, "26c940a1-7228-4ea2-a3bc-e6460b172040", 0
        )
        assert client_status["id"] == "26c940a1-7228-4ea2-a3bc-e6460b172040"
        assert client_status["name"] == "Петров Иван Сергеевич"
        assert client_status["balance"] == 1700
        assert client_status["hold"] == 300
        assert client_status["is_open"] is True

        # запрос со снятием на отрицательное число денег тоже не изменяет ничего
        client_status = await query_subtract(
            connection, "26c940a1-7228-4ea2-a3bc-e6460b172040", -1000
        )
        assert client_status["balance"] == 1700
        assert client_status["hold"] == 300

        # если попытаться снять больше, чем у клиента есть денег на счёте,
        # то произойдет исключение
        with pytest.raises(NotEnoughMoneyError):
            await query_subtract(
                connection, "26c940a1-7228-4ea2-a3bc-e6460b172040", 2000
            )
        # при этом данные не изменятся
        client_status = await query_status(
            connection, "26c940a1-7228-4ea2-a3bc-e6460b172040"
        )
        assert client_status["balance"] == 1700
        assert client_status["hold"] == 300

        # успешный запрос
        client_status = await query_subtract(
            connection, "26c940a1-7228-4ea2-a3bc-e6460b172040", 100
        )
        assert client_status["balance"] == 1700  # баланс не изменился
        assert client_status["hold"] == 400  # увеличился холд

        # снятие денег с закрытого счёта возвращает None
        client_status = await query_subtract(
            connection, "867f0924-a917-4711-939b-90b179a96392", 1000
        )
        assert client_status is None
        # баланс счёта не изменился
        client_status = await query_status(
            connection, "867f0924-a917-4711-939b-90b179a96392"
        )
        assert client_status["balance"] == 1_000_000

    async def test_unhold_all(self, test_data, connection: asyncpg.Connection) -> None:
        """Проверить функцию, обновляющую баланс клиентов и очищающую холды.

        :param test_data: добавить тестовые данные в таблицу
        :param connection: соединение к базе
        """
        await query_unhold_all(connection)

        expected_balance = {
            "26c940a1-7228-4ea2-a3bc-e6460b172040": 1400,
            "7badc8f8-65bc-449a-8cde-855234ac63e1": 0,
            "5597cc3d-c948-48a0-b711-393edf20d9c0": -290,
            "867f0924-a917-4711-939b-90b179a96392": 999_999,
        }

        for uuid, balance in expected_balance.items():
            client_status = await query_status(connection, uuid)
            assert client_status["balance"] == balance
            assert client_status["hold"] == 0
