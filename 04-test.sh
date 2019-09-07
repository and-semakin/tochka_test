#!/bin/bash
command -v docker-compose >/dev/null 2>&1 || { echo >&2 "This script requires `docker-compose` but it's not installed.  Aborting."; exit 1; }
echo "==== Tests (pytest) ===="
docker-compose exec api pipenv run python -m pytest
echo "==== Type-checker (mypy) ===="
docker-compose exec api pipenv run mypy app
echo "==== Linter (flake8) ===="
docker-compose exec api pipenv run flake8 app
echo "==== Code-style & formatting (black) ===="
docker-compose exec api pipenv run black --check app
