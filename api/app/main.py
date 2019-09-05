from typing import List
import random
import asyncpg
from aiohttp import web

from .settings import Settings


async def startup(app: web.Application):
    settings: Settings = app['settings']
    app['pg'] = await asyncpg.create_pool(dsn=settings.pg_dsn, min_size=2)


async def cleanup(app: web.Application):
    await app['pg'].close()


async def ping(*args):
    answers: List[str] = [
        "I'm ok!",
        "I'm fine!",
        "I am still alive!",
        "Don't hurt me please",
    ]
    return web.json_response({
        'status': 'ok',
        'answer': random.choice(answers),
    }, status=200)


async def kill():
    # TODO: implement
    pass


async def add():
    # TODO: implement
    pass


async def subtract():
    # TODO: implement
    pass


async def status():
    # TODO: implement
    pass


async def create_app():
    app = web.Application()
    settings = Settings()
    app.update(
        settings=settings,
    )

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)

    app.router.add_get('/api/ping', ping, name='ping')
    app.router.add_get('/api/kill', kill, name='kill')
    app.router.add_post('/api/add', add, name='add')
    app.router.add_post('/api/subtract', subtract, name='subtract')
    app.router.add_get('/api/status', status, name='status')
    return app
