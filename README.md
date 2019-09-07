# Тестовое задание

API для хранения информации о состоянии счетов абонентов. Позволяет производить операции со счетами, получать текущие параметры счестов абонентов.

## Как запустить:
```sh
./01-build.sh
./02-deploy.sh
./03-create-tables.sh
``` 

После этого по адресу http://localhost:80/ будет доступно API.

## Эндпоинты API:
* `/api/ping` -- работоспособность сервиса;
* `/api/add` -- пополнение баланса;
* `/api/subtract` -- уменьшение баланса;
* `/api/status` -- остаток по балансу, открыт счёт или закрыт.

### Запустить тесты
/* TODO implement */
```sh
./04-run-tests.sh
```

/* TODO add usage examples */