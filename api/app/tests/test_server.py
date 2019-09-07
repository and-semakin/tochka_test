from typing import Callable, Any, List, Mapping

import pytest

from app.main import _check_args


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
