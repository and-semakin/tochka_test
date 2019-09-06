from typing import Callable, Any, List, Mapping
import functools
import asyncio

import pytest
import asyncpg
import aiohttp

from app.main import _check_args, create_app
from app.settings import Settings


def run_until_complete(function: Callable) -> Callable:
    """Декоратор выполняющий функцию в евентлупе."""

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Выполняем функцию в евентлупе."""
        return asyncio.get_event_loop().run_until_complete(function(*args, **kwargs))

    return wrapper


async def handler_a(
    request: Any, a: int, b: str, c: float, d: bool, e: type(None)
) -> int:
    """Хэндлер для теста."""
    pass


async def handler_b(request: Any, a: list, b: dict):
    """Хэндлер для теста."""
    pass


class TestServerUtils:
    @pytest.mark.parametrize(
        ("handler", "json_data", "expected_errors"),
        [
            (  # успешный пример
                handler_a,
                {"a": 1, "b": "b", "c": 3.14, "d": False, "e": None},
                [],
            ),
            (  # не хватает одного аргумента
                handler_a,
                {"b": "b", "c": 3.14, "d": False, "e": None},
                ["a is required but it is missing"],
            ),
            (  # не тот тип аргумента
                handler_a,
                {"a": "qwe", "b": "b", "c": 3.14, "d": False, "e": None},
                ["Expected type of a is int, but str was passed"],
            ),
            (  # лишний аргумент
                handler_a,
                {"a": 1, "b": "b", "c": 3.14, "d": False, "e": None, "f": "redundant"},
                ["Redundant arg f"],
            ),
            (  # ещё один успешный пример, но со сложными типами данных
                handler_b,
                {"a": [], "b": {}},
                [],
            ),
            (  # ещё один успешный пример, порядок в словаре не имеет значения
                handler_b,
                {"b": {}, "a": []},
                [],
            ),
            (  # типы аргументов перепутаны
                handler_b,
                {"a": {}, "b": []},
                [
                    "Expected type of a is list, but dict was passed",
                    "Expected type of b is dict, but list was passed",
                ],
            ),
        ],
    )
    def test_check_args(
        self,
        handler: Callable,
        json_data: Mapping[str, Any],
        expected_errors: List[str],
    ) -> None:
        """Тест функции, проверяющей типы и наличие аргументов для хэндлера."""
        errors = _check_args(handler, json_data)
        assert errors == expected_errors, "Ошибки не совпали с ожидаемыми"


test_settings = Settings()


@pytest.mark.asyncio
class TestServer:
    """Интеграционные тесты, проверяющие работу API."""

    @staticmethod
    @run_until_complete
    async def setup_class() -> None:
        """До начала тестов копируем базу и очищаем таблицу client."""
        connection = await asyncpg.connect(dsn=test_settings.pg_dsn)
        try:
            await connection.execute(f'DROP DATABASE IF EXISTS {test_settings.postgres_test_db}')
            await connection.execute(
                '''
                SELECT
                    pg_terminate_backend(pg_stat_activity.pid)
                FROM
                    pg_stat_activity
                WHERE
                    pg_stat_activity.datname = $1 AND
                    pid <> pg_backend_pid();
                ''',
                test_settings.postgres_db
            )
            await connection.execute(f'CREATE DATABASE {test_settings.postgres_test_db} WITH TEMPLATE {test_settings.postgres_db}')
        finally:
            await connection.close()

    @pytest.fixture()
    async def connection(self) -> asyncpg.Connection:
        connection = await asyncpg.connect(dsn=test_settings.pg_test_dsn)
        try:
            yield connection
        finally:
            await connection.close()

    @pytest.fixture()
    async def test_data(self, connection) -> None:
        await connection.execute('TRUNCATE client')
        await connection.execute(
            '''
            INSERT INTO client
                   (id, name, balance, hold, is_open)
            VALUES
                   ('26c940a1-7228-4ea2-a3bc-e6460b172040', 'Петров Иван Сергеевич', 1700, 300, TRUE),
                   ('7badc8f8-65bc-449a-8cde-855234ac63e1', 'Kazitsky Jason', 200, 200, TRUE),
                   ('5597cc3d-c948-48a0-b711-393edf20d9c0', 'Пархоменко Антон Александрович', 10, 300, TRUE),
                   ('867f0924-a917-4711-939b-90b179a96392', 'Петечкин Петр Измаилович', 1000000, 1, FALSE);

            '''
        )

    @pytest.fixture(scope="function")
    async def client(self, aiohttp_client, event_loop) -> aiohttp.ClientSession:
        settings = test_settings.copy()
        settings.postgres_db = settings.postgres_test_db
        app = await create_app(settings)
        client = await (await aiohttp_client(event_loop))(app)
        try:
            yield client
        finally:
            await app.shutdown()
            await app.cleanup()
            await asyncio.sleep(0.5)

    async def test_ping(self, client: aiohttp.ClientSession) -> None:
        resp = await asyncio.wait_for(client.get('/api/ping'), 5)
        assert resp.status == 200

    async def test_status(self) -> None:
        pass

    async def test_add(self) -> None:
        pass

    async def test_subtract(self) -> None:
        pass
