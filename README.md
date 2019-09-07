# Тестовое задание

API для хранения информации о состоянии счетов абонентов. Позволяет производить операции со счетами, получать текущие параметры счестов абонентов.

## Как запустить:
```sh
./01-build.sh
./02-deploy.sh
./03-create-tables.sh
``` 

Опционально, можно запустить тесты:
```sh
./04-test.sh
```

После этого по адресу http://localhost:80/ будет доступно API.

## Эндпоинты API:
* `/api/ping` -- работоспособность сервиса;
* `/api/add` -- пополнение баланса;
* `/api/subtract` -- уменьшение баланса;
* `/api/status` -- остаток по балансу, открыт счёт или закрыт;
* `/api/kill` -- убивает сервис; можно использовать, чтобы проверить перезапуск контейнера. 

API имеет примитивную валидацию данных в JSON, поэтому требуется передавать указанные ключи с нужными типами данных.
Чаще всего требуется два ключа: строка `uuid` и целое `how_much` (количество копеек для операции).

### Примеры использования:

```sh
# ping
$ curl http://localhost/api/ping
{ 
   "status":200,
   "result":true,
   "addition":null,
   "description":"I am still alive!"
}


# status
$ curl --header "Content-Type: application/json" \
   --request POST \
   --data '{"uuid":"26c940a1-7228-4ea2-a3bc-e6460b172040"}' \
   http://localhost/api/status
{ 
   "status":200,
   "result":true,
   "addition":{ 
      "id":"26c940a1-7228-4ea2-a3bc-e6460b172040",
      "name":"Петров Иван Сергеевич",
      "balance":1700,
      "hold":300,
      "is_open":true
   },
   "description":""
}


# add
$ curl --header "Content-Type: application/json" \
   --request POST \
   --data '{"uuid":"26c940a1-7228-4ea2-a3bc-e6460b172040","how_much":100}' \
   http://localhost/api/add
{ 
   "status":200,
   "result":true,
   "addition":{ 
      "id":"26c940a1-7228-4ea2-a3bc-e6460b172040",
      "name":"Петров Иван Сергеевич",
      "balance":1800,
      "hold":300,
      "is_open":true
   },
   "description":""
}


# subtract
$ curl --header "Content-Type: application/json" \
   --request POST \
   --data '{"uuid":"26c940a1-7228-4ea2-a3bc-e6460b172040","how_much":1000}' \
   http://localhost/api/subtract
{ 
   "status":200,
   "result":true,
   "addition":{ 
      "id":"26c940a1-7228-4ea2-a3bc-e6460b172040",
      "name":"Петров Иван Сергеевич",
      "balance":1800,
      "hold":1300,
      "is_open":true
   },
   "description":""
}
```