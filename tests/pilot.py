"""Тестовый пилот делегирует команды публичному интерфейсу транспорта."""

from typing import Any


class Pilot:
    """Управляет транспортом без собственной модели его состояния."""

    def __init__(self, vehicle: Any) -> None:
        self._vehicle = vehicle

    def travel(self, distance_km: float, terrain: str) -> float:
        return self._vehicle.move(distance_km, terrain)

    def estimate(self, distance_km: float, terrain: str) -> float:
        return self._vehicle.calculate_energy(distance_km, terrain)

    def roll_up(self) -> None:
        return self._vehicle.fold_shell()

    def open_shell(self) -> None:
        return self._vehicle.unfold_shell()

    def recharge(self, amount: float) -> None:
        return self._vehicle.refuel(amount)

    def status(self) -> dict[str, str | float]:
        return self._vehicle.get_status()
