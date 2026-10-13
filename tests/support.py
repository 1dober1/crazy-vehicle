"""Общие проверки публичного контракта без доступа к реализации."""

import importlib
import unittest
from typing import Any, Callable


class ContractTestCase(unittest.TestCase):
    """Загружает модуль транспорта и проверяет публичное состояние."""

    def setUp(self) -> None:
        self.contract = importlib.import_module("basalt_snail")
        self.vehicle_class = self.contract.BasaltSnail

    def make_vehicle(self, **parameters: Any) -> Any:
        arguments = {"name": "Улитка-1", "mass_kg": 200.0}
        arguments.update(parameters)
        return self.vehicle_class(**arguments)

    def public_state(self, vehicle: Any) -> dict[str, str | float]:
        return {
            attribute: getattr(vehicle, attribute)
            for attribute in (
                "name",
                "mass_kg",
                "wheel_diameter_m",
                "energy",
                "distance_km",
                "mode",
            )
        }

    def expected_state(
        self,
        energy: float = 100.0,
        distance_km: float = 0.0,
        mode: str = "crawl",
        name: str = "Улитка-1",
        mass_kg: float = 200.0,
        wheel_diameter_m: float = 1.0,
    ) -> dict[str, str | float]:
        return {
            "name": name,
            "mass_kg": mass_kg,
            "wheel_diameter_m": wheel_diameter_m,
            "energy": energy,
            "distance_km": distance_km,
            "mode": mode,
        }

    def assert_state(
        self,
        actual: dict[str, str | float],
        expected: dict[str, str | float],
    ) -> None:
        self.assertIs(type(actual), dict)
        self.assertEqual(set(actual), set(expected))
        for attribute, expected_value in expected.items():
            with self.subTest(attribute=attribute):
                self.assertIs(type(actual[attribute]), type(expected_value))
                if isinstance(expected_value, float):
                    self.assertAlmostEqual(actual[attribute], expected_value, places=7)
                else:
                    self.assertEqual(actual[attribute], expected_value)

    def assert_result(self, actual: float, expected: float) -> None:
        self.assertIs(type(actual), float)
        self.assertAlmostEqual(actual, expected, places=7)

    def assert_error(
        self,
        error_class: type[Exception],
        message: str,
        action: Callable[[], Any],
    ) -> None:
        with self.assertRaises(error_class) as caught:
            action()
        self.assertIs(type(caught.exception), error_class)
        self.assertEqual(str(caught.exception), message)

    def assert_atomic_error(
        self,
        vehicle: Any,
        error_class: type[Exception],
        message: str,
        action: Callable[[], Any],
    ) -> None:
        before = self.public_state(vehicle)
        self.assert_error(error_class, message, action)
        self.assert_state(self.public_state(vehicle), before)
