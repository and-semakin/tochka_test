import argparse
import asyncio
import enum
import logging

from aiohttp import web

from app.main import create_app
from app.unholder import periodic_unhold_all


logging.basicConfig(level=logging.INFO)


class Mode(enum.Enum):
    SERVER = "server"
    UNHOLDER = "unholder"

    def __str__(self):
        return self.value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=Mode, choices=list(Mode))
    args = parser.parse_args()

    logging.info(f"Starting {args.mode}...")
    if args.mode == Mode.SERVER:
        web.run_app(create_app(), port=80)
    elif args.mode == Mode.UNHOLDER:
        asyncio.run(periodic_unhold_all())
    else:
        raise NotImplementedError


if __name__ == "__main__":
    main()
