from typing import Any, List, Callable, Mapping
import sys
import random
import functools
import json
import inspect
import logging

import asyncpg
from aiohttp import web

from app.settings import Settings


def json_response(
    addition: Any = None,
    operation_status: bool = True,
    description: str = "",
    status: int = 200,
    **kwargs,
) -> web.Response:
    """JSON ответ, сформированный по шаблону.

    :param addition: данные для ответа
    :param operation_status: успешна ли операция
    :param description: текстовое описание ответа
    :param status: HTTP код ответа
    """
    return web.json_response(
        {
            "status": status,
            "result": operation_status,
            "addition": addition,
            "description": description,
        },
        status=status,
        dumps=functools.partial(json.dumps, ensure_ascii=False),
        **kwargs,
    )


async def init_connection(conn: asyncpg.Connection) -> None:
    """Инициализация отдельного соединения в пуле."""
    # делаем так, чтобы тип UUID преобразовывался в строку при извлечении из базы
    await conn.set_type_codec("uuid", encoder=str, decoder=str, schema="pg_catalog")


async def startup(app: web.Application) -> None:
    """Инициализация приложения."""
    settings: Settings = app["settings"]
    app["pg"] = await asyncpg.create_pool(
        dsn=settings.pg_dsn, min_size=2, init=init_connection
    )


async def cleanup(app: web.Application):
    """Завершение работы приложения."""
    await app["pg"].close()


async def ping(request: web.Request) -> web.Response:
    answers: List[str] = [
        "I'm ok!",
        "I'm fine!",
        "I am still alive!",
        "Don't hurt me please",
    ]
    return json_response(operation_status=True, description=random.choice(answers))


async def kill(request: web.Request) -> web.Response:
    """Хэндлер, который убивает сервер, чтобы проверить настройку перезапуска."""
    sys.exit(42)


async def add(request: web.Request, uuid: str, how_much: int) -> web.Response:
    """Пополнить баланс указанного пользователя.

    :param request: запрос
    :param uuid: идентификатор пользователя
    :param how_much: количество копеек, которые нужно прибавить на баланс пользователя
    """
    async with request.app["pg"].acquire() as connection:
        async with connection.transaction():
            row: asyncpg.Record = await connection.fetchrow(
                """
                UPDATE
                    client
                SET
                    balance = balance + $2
                WHERE
                    id = $1
                RETURNING *
                """,
                uuid,
                how_much,
            )
            if not row:
                raise web.HTTPNotFound()
            return json_response(dict(row.items()))


async def subtract(request: web.Request, uuid: str, how_much: int) -> web.Response:
    """Пополнить баланс указанного пользователя.

    :param request: запрос
    :param uuid: идентификатор пользователя
    :param how_much: количество копеек, которые нужно снять с баланса пользователя
    """
    async with request.app["pg"].acquire() as connection:
        async with connection.transaction():
            row: asyncpg.Record = await connection.fetchrow(
                """
                UPDATE
                    client
                SET
                    balance = balance - $2,
                    hold = hold + $2
                WHERE
                    id = $1
                RETURNING *
                """,
                uuid,
                how_much,
            )
            if not row:
                raise web.HTTPNotFound()
            if row["balance"] < 0:
                raise web.HTTPPaymentRequired()
            return json_response(dict(row.items()))


async def status(request: web.Request, uuid: str) -> web.Response:
    """Получить данные о текущем состоянии счетов клиентов."""
    async with request.app["pg"].acquire() as connection:
        row: asyncpg.Record = await connection.fetchrow(
            """
            SELECT * FROM client WHERE id = $1
            """,
            uuid,
        )
        if not row:
            raise web.HTTPNotFound()
        return json_response(dict(row.items()))


def _check_args(handler: Callable, args: Mapping[str, Any]) -> List[str]:
    """Функция, которая валидирует переданные через JSON аргументы.

    :param handler: хэндлер
    :param args: словарь с аргументами из JSON
    :returns: список ошибок; если ошибок нет, то список пустой
    """
    errors = []

    # получаем информацию о сигнатуре хэндлера
    handler_fullargspec = inspect.getfullargspec(handler)

    # проходимся по аргументами хэндлера
    for arg, expected_type in handler_fullargspec.annotations.items():
        # `request` -- обязательный аргумент хэндлера, но он поступает не из JSON
        # `return` -- зарезервированное значение для аннотации возвращаемого значения
        if arg in ("request", "return"):
            continue

        if arg not in args:
            errors.append(f"{arg} is required but it is missing")
            continue

        value = args[arg]
        if not isinstance(value, expected_type):
            errors.append(
                f"Expected type of {arg} is {expected_type.__name__}, "
                f"but {type(value).__name__} was passed"
            )

    # если в JSON содержатся лишние данные, то это тоже проблема
    for arg, value in args.items():
        if arg not in handler_fullargspec.args:
            errors.append(f"Redundant arg {arg}")

    return errors


@web.middleware
async def json_middleware(request: web.Request, handler) -> web.Response:
    """Требовать наличия JSON содержимого во всех запросах, кроме GET."""
    if request.method == "GET":
        return await handler(request)

    try:
        json_data = await request.json()
    except json.decoder.JSONDecodeError:
        return json_response(
            status=400,
            operation_status=False,
            description="Please send request in JSON format",
        )

    errors = _check_args(handler, json_data)
    if not errors:
        return await handler(request, **json_data)

    return json_response(
        status=400, operation_status=False, description="; ".join(errors)
    )


@web.middleware
async def error_middleware(request: web.Request, handler) -> web.Response:
    """Миддлварь, которая вместо стэктрейсов отдаст на клиент JSON."""
    try:
        return await handler(request)
    except web.HTTPError as exc:
        return json_response(
            status=exc.status, operation_status=False, description=exc.reason
        )
    except Exception:
        logging.exception("Unhandled error")
        return json_response(
            status=500, operation_status=False, description="Internal Server Error"
        )


async def create_app() -> web.Application:
    """Создать и настроить приложение aiohttp."""
    app = web.Application(middlewares=[error_middleware, json_middleware])
    settings = Settings()
    app.update(settings=settings)

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)

    # маршрутизация
    app.router.add_get("/api/ping", ping, name="ping")
    app.router.add_get("/api/kill", kill, name="kill")
    app.router.add_post("/api/add", add, name="add")  # type: ignore
    app.router.add_post("/api/subtract", subtract, name="subtract")  # type: ignore
    app.router.add_post("/api/status", status, name="status")  # type: ignore
    return app
