import argparse
import asyncio

from aiohttp import web

from .main import create_app
from .subtractor import periodic_subtract

SERVER = "server"
SUBTRACTOR = "subtractor"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=[SERVER, SUBTRACTOR])
    args = parser.parse_args()

    if args.mode == SERVER:
        web.run_app(create_app())
    elif args.mode == SUBTRACTOR:
        asyncio.run(periodic_subtract())
    else:
        raise NotImplementedError


if __name__ == "__main__":
    main()
