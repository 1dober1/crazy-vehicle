"""Сквозные Given–When–Then сценарии SPEC 1.0.0 через тестового пилота."""

from typing import Any, Callable

from tests.pilot import Pilot
from tests.support import ContractTestCase


class BasaltSnailScenarioTests(ContractTestCase):
    """Проверяет последовательности команд и полный статус через пилота."""

    def assert_pilot_state(
        self,
        pilot: Pilot,
        energy: float,
        distance_km: float,
        mode: str = "crawl",
        mass_kg: float = 200.0,
        wheel_diameter_m: float = 1.0,
    ) -> None:
        self.assert_state(
            pilot.status(),
            self.expected_state(
                energy=energy, distance_km=distance_km, mode=mode,
                mass_kg=mass_kg, wheel_diameter_m=wheel_diameter_m,
            ),
        )

    def assert_pilot_error(
        self,
        pilot: Pilot,
        error_class: type[Exception],
        message: str,
        action: Callable[[], Any],
    ) -> None:
        before = pilot.status()
        self.assert_error(error_class, message, action)
        self.assert_state(pilot.status(), before, exact=True)

    def test_TC_S_01_mixed_terrain_delivery(self) -> None:
        """TC_S_01: Given обычная улитка; When три грунта; Then доставка."""
        pilot = Pilot(self.make_vehicle())
        self.assert_pilot_state(pilot, 100.0, 0.0)

        duration = pilot.travel(2.0, "road")

        self.assert_result(duration, 0.2)
        self.assert_pilot_state(pilot, 90.0, 2.0)

        duration = pilot.travel(1.0, "rock")

        self.assert_result(duration, 0.2)
        self.assert_pilot_state(pilot, 80.0, 3.0)

        duration = pilot.travel(1.0, "sand")

        self.assert_result(duration, 0.5)
        self.assert_pilot_state(pilot, 65.0, 4.0)

    def test_TC_S_02_fast_road_then_rocks(self) -> None:
        """TC_S_02: Given дорога и камни; When смены режима; Then маршрут."""
        pilot = Pilot(self.make_vehicle())

        self.assertIsNone(pilot.roll_up())
        self.assert_pilot_state(pilot, 90.0, 0.0, "roll")

        duration = pilot.travel(1.0, "road")

        self.assert_result(duration, 0.025)
        self.assert_pilot_state(pilot, 85.0, 1.0, "roll")

        self.assertIsNone(pilot.open_shell())
        self.assert_pilot_state(pilot, 80.0, 1.0)

        duration = pilot.travel(2.0, "rock")

        self.assert_result(duration, 0.4)
        self.assert_pilot_state(pilot, 60.0, 3.0)

    def test_TC_S_03_rescue_after_discharge(self) -> None:
        """TC_S_03: Given заряд 20; When разряд и спасение; Then атомарные отказы."""
        pilot = Pilot(self.make_vehicle(energy=20.0))

        duration = pilot.travel(2.0, "rock")

        self.assert_result(duration, 0.4)
        self.assert_pilot_state(pilot, 0.0, 2.0)
        self.assert_pilot_error(
            pilot, self.contract.InsufficientEnergyError,
            "not enough energy to fold shell", pilot.roll_up,
        )

        self.assertIsNone(pilot.recharge(15.0))
        self.assert_pilot_state(pilot, 15.0, 2.0)
        self.assertIsNone(pilot.roll_up())
        self.assert_pilot_state(pilot, 5.0, 2.0, "roll")

        duration = pilot.travel(1.0, "road")

        self.assert_result(duration, 0.025)
        self.assert_pilot_state(pilot, 0.0, 3.0, "roll")
        self.assert_pilot_error(
            pilot, self.contract.InsufficientEnergyError,
            "not enough energy to unfold shell", pilot.open_shell,
        )

    def test_TC_S_04_station_and_sand_detour(self) -> None:
        """TC_S_04: Given заряд 25; When станция и песок; Then заряд ограничен."""
        pilot = Pilot(self.make_vehicle(energy=25.0))

        self.assertIsNone(pilot.roll_up())
        self.assert_pilot_state(pilot, 15.0, 0.0, "roll")

        duration = pilot.travel(3.0, "road")

        self.assert_result(duration, 0.075)
        self.assert_pilot_state(pilot, 0.0, 3.0, "roll")
        self.assertIsNone(pilot.recharge(200.0))
        self.assert_pilot_state(pilot, 100.0, 3.0, "roll")
        self.assertIsNone(pilot.open_shell())
        self.assert_pilot_state(pilot, 95.0, 3.0)

        duration = pilot.travel(2.0, "sand")

        self.assert_result(duration, 1.0)
        self.assert_pilot_state(pilot, 65.0, 5.0)

    def test_TC_S_05_shell_locked_without_energy(self) -> None:
        """TC_S_05: Given заряд 10; When блокировка; Then приоритет и раскрытие."""
        pilot = Pilot(self.make_vehicle(energy=10.0))

        self.assertIsNone(pilot.roll_up())
        self.assert_pilot_state(pilot, 0.0, 0.0, "roll")
        self.assert_pilot_error(
            pilot, self.contract.ShellStateError,
            "shell is already folded", pilot.roll_up,
        )
        self.assert_pilot_error(
            pilot, self.contract.RollingTerrainError,
            "rolling is only allowed on road", lambda: pilot.travel(1.0, "rock"),
        )
        self.assert_pilot_error(
            pilot, self.contract.InsufficientEnergyError,
            "not enough energy to unfold shell", pilot.open_shell,
        )

        self.assertIsNone(pilot.recharge(5.0))
        self.assert_pilot_state(pilot, 5.0, 0.0, "roll")
        self.assertIsNone(pilot.open_shell())
        self.assert_pilot_state(pilot, 0.0, 0.0)

    def test_TC_S_06_heavy_snail_large_wheels(self) -> None:
        """TC_S_06: Given масса 400 и колёса 2; When поездка; Then свои расходы."""
        pilot = Pilot(self.make_vehicle(mass_kg=400.0, wheel_diameter_m=2.0))
        characteristics = {"mass_kg": 400.0, "wheel_diameter_m": 2.0}

        cost = pilot.estimate(1.0, "rock")

        self.assert_result(cost, 20.0)
        self.assert_pilot_state(pilot, 100.0, 0.0, **characteristics)

        duration = pilot.travel(1.0, "road")

        self.assert_result(duration, 0.05)
        self.assert_pilot_state(pilot, 90.0, 1.0, **characteristics)
        self.assertIsNone(pilot.roll_up())
        self.assert_pilot_state(pilot, 80.0, 1.0, "roll", **characteristics)

        duration = pilot.travel(2.0, "road")

        self.assert_result(duration, 0.025)
        self.assert_pilot_state(pilot, 60.0, 3.0, "roll", **characteristics)
        self.assertIsNone(pilot.open_shell())
        self.assert_pilot_state(pilot, 55.0, 3.0, **characteristics)

        duration = pilot.travel(1.0, "rock")

        self.assert_result(duration, 0.1)
        self.assert_pilot_state(pilot, 35.0, 4.0, **characteristics)

    def test_TC_S_07_terrain_rejections_and_recovery(self) -> None:
        """TC_S_07: Given заряд 30; When отказы сред; Then маршрут продолжается."""
        pilot = Pilot(self.make_vehicle(energy=30.0))

        self.assertIsNone(pilot.roll_up())
        self.assert_pilot_state(pilot, 20.0, 0.0, "roll")

        duration = pilot.travel(1.0, "road")

        self.assert_result(duration, 0.025)
        self.assert_pilot_state(pilot, 15.0, 1.0, "roll")
        for terrain in ("water", "air"):
            with self.subTest(terrain=terrain):
                self.assert_pilot_error(
                    pilot, self.contract.UnsupportedTerrainError,
                    "basalt snail can only travel on land",
                    lambda: pilot.travel(1.0, terrain),
                )
        self.assert_pilot_error(
            pilot, self.contract.RollingTerrainError,
            "rolling is only allowed on road", lambda: pilot.travel(1.0, "rock"),
        )

        self.assertIsNone(pilot.recharge(10.0))
        self.assert_pilot_state(pilot, 25.0, 1.0, "roll")
        self.assertIsNone(pilot.open_shell())
        self.assert_pilot_state(pilot, 20.0, 1.0)

        duration = pilot.travel(1.0, "rock")

        self.assert_result(duration, 0.2)
        self.assert_pilot_state(pilot, 10.0, 2.0)

    def test_TC_S_08_retry_after_recharge(self) -> None:
        """TC_S_08: Given заряд 12; When отказ и дозарядка; Then повтор успешен."""
        pilot = Pilot(self.make_vehicle(energy=12.0))

        self.assertIsNone(pilot.roll_up())
        self.assert_pilot_state(pilot, 2.0, 0.0, "roll")

        cost = pilot.estimate(1.0, "road")

        self.assert_result(cost, 5.0)
        self.assert_pilot_state(pilot, 2.0, 0.0, "roll")
        self.assert_pilot_error(
            pilot, self.contract.InsufficientEnergyError,
            "not enough energy to move", lambda: pilot.travel(1.0, "road"),
        )

        self.assertIsNone(pilot.recharge(3.0))
        self.assert_pilot_state(pilot, 5.0, 0.0, "roll")

        duration = pilot.travel(1.0, "road")

        self.assert_result(duration, 0.025)
        self.assert_pilot_state(pilot, 0.0, 1.0, "roll")
        self.assert_pilot_state(pilot, 0.0, 1.0, "roll")
