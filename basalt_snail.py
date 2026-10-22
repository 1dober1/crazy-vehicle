"""Наземная панцирная машина «Базальтовая Улитка».

Реализация публичного контракта SPEC.md версии 1.0.0.
"""

from __future__ import annotations

import math

__all__ = [
    "BasaltSnail",
    "BasaltSnailError",
    "CrazyVehicleError",
    "InsufficientEnergyError",
    "RollingTerrainError",
    "ShellStateError",
    "UnsupportedTerrainError",
]


# ---------------------------------------------------------------------------
# Исключения (SPEC 6.1)
# ---------------------------------------------------------------------------


class CrazyVehicleError(Exception):
    """Базовая ошибка любого безумного транспорта."""


class BasaltSnailError(CrazyVehicleError):
    """Базовая доменная ошибка «Базальтовой Улитки»."""


class UnsupportedTerrainError(BasaltSnailError):
    """Попытка движения по воде или воздуху."""


class RollingTerrainError(BasaltSnailError):
    """Попытка движения по камням или песку в свёрнутом режиме."""


class InsufficientEnergyError(BasaltSnailError):
    """Недостаточно энергии для действия."""


class ShellStateError(BasaltSnailError):
    """Панцирь уже находится в запрошенном состоянии."""


# ---------------------------------------------------------------------------
# Константы домена (SPEC 2, 3.4)
# ---------------------------------------------------------------------------

CRAWL = "crawl"
ROLL = "roll"

LAND_TERRAINS = ("road", "rock", "sand")
NON_LAND_TERRAINS = ("water", "air")
KNOWN_TERRAINS = LAND_TERRAINS + NON_LAND_TERRAINS
ROLL_TERRAINS = ("road",)

ENERGY_PER_KM = {"road": 5.0, "rock": 10.0, "sand": 15.0}
REFERENCE_MASS_KG = 200.0

SPEED_PER_METER_OF_WHEEL = {
    (CRAWL, "road"): 10.0,
    (CRAWL, "rock"): 5.0,
    (CRAWL, "sand"): 2.0,
    (ROLL, "road"): 40.0,
}

FOLD_COST = 10.0
UNFOLD_COST = 5.0
MAX_ENERGY = 100.0

MASS_RANGE = (100.0, 500.0)
WHEEL_RANGE = (0.5, 2.0)
ENERGY_RANGE = (0.0, MAX_ENERGY)


# ---------------------------------------------------------------------------
# Проверка параметров (SPEC 3.2, 6.2)
# ---------------------------------------------------------------------------


def _require_number(value: object, name: str) -> None:
    """Проверяет, что значение — int или float, но не bool."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")


def _to_finite_float(value: int | float, message: str) -> float:
    """Приводит число к float; неконечное значение → ValueError."""
    try:
        result = float(value)
    except OverflowError:
        raise ValueError(message) from None
    if not math.isfinite(result):
        raise ValueError(message)
    return result


def _number_in_range(
    value: object, name: str, bounds: tuple[float, float], message: str
) -> float:
    """Проверяет тип, конечность и включённый диапазон числа."""
    _require_number(value, name)
    lower, upper = bounds
    # Целые сравниваются без перевода в float, чтобы огромные int
    # давали ValueError, а не OverflowError.
    if isinstance(value, int) and not lower <= value <= upper:
        raise ValueError(message)
    result = _to_finite_float(value, message)  # type: ignore[arg-type]
    if not lower <= result <= upper:
        raise ValueError(message)
    return result


def _positive_number(value: object, name: str) -> float:
    """Проверяет тип, конечность и строгую положительность числа."""
    _require_number(value, name)
    message = f"{name} must be finite and positive"
    result = _to_finite_float(value, message)  # type: ignore[arg-type]
    if result <= 0.0:
        raise ValueError(message)
    return result


# ---------------------------------------------------------------------------
# Транспорт
# ---------------------------------------------------------------------------


class BasaltSnail:
    """Одноместная наземная машина с каменными колёсами и панцирем.

    Режим ``crawl``: панцирь раскрыт, доступны ``road``, ``rock``, ``sand``.
    Режим ``roll``: панцирь свёрнут, доступна только ``road``.
    Все публичные атрибуты доступны только для чтения.
    """

    __slots__ = (
        "_name",
        "_mass_kg",
        "_wheel_diameter_m",
        "_energy",
        "_distance_km",
        "_mode",
    )

    def __init__(
        self,
        name: str,
        mass_kg: float,
        wheel_diameter_m: float = 1.0,
        energy: float = 100.0,
    ) -> None:
        """Создаёт транспорт в режиме ``crawl`` с нулевым пробегом.

        Raises:
            TypeError: неверный тип параметра.
            ValueError: пустое имя или число вне допустимого диапазона.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("name must not be empty")

        mass = _number_in_range(
            mass_kg, "mass_kg", MASS_RANGE,
            "mass_kg must be finite and between 100 and 500",
        )
        diameter = _number_in_range(
            wheel_diameter_m, "wheel_diameter_m", WHEEL_RANGE,
            "wheel_diameter_m must be finite and between 0.5 and 2",
        )
        start_energy = _number_in_range(
            energy, "energy", ENERGY_RANGE,
            "energy must be finite and between 0 and 100",
        )

        self._name: str = normalized_name
        self._mass_kg: float = mass
        self._wheel_diameter_m: float = diameter
        self._energy: float = start_energy
        self._distance_km: float = 0.0
        self._mode: str = CRAWL

    # --- Публичные атрибуты только для чтения (SPEC 3.3) -------------------

    @property
    def name(self) -> str:
        """Нормализованное имя."""
        return self._name

    @property
    def mass_kg(self) -> float:
        """Масса, кг."""
        return self._mass_kg

    @property
    def wheel_diameter_m(self) -> float:
        """Диаметр колёс, м."""
        return self._wheel_diameter_m

    @property
    def energy(self) -> float:
        """Текущий запас энергии, 0…100."""
        return self._energy

    @property
    def distance_km(self) -> float:
        """Общий пройденный путь, км."""
        return self._distance_km

    @property
    def mode(self) -> str:
        """Режим панциря: ``crawl`` или ``roll``."""
        return self._mode

    # --- Движение (SPEC 3.4.1, 3.4.2) --------------------------------------

    def _checked_route(self, distance_km: object, terrain: object) -> float:
        """Проверяет параметры и среду, возвращает дистанцию как float.

        Порядок проверок по SPEC 3.4.2, пункты 1–4.
        """
        distance = _positive_number(distance_km, "distance_km")

        if not isinstance(terrain, str):
            raise TypeError("terrain must be a string")
        if terrain not in KNOWN_TERRAINS:
            raise ValueError("unknown terrain")

        if terrain in NON_LAND_TERRAINS:
            raise UnsupportedTerrainError(
                "basalt snail can only travel on land"
            )
        if self._mode == ROLL and terrain not in ROLL_TERRAINS:
            raise RollingTerrainError("rolling is only allowed on road")

        return distance

    def _cost(self, distance: float, terrain: str) -> float:
        """Расход энергии; группировка операций задана SPEC 3.4.1."""
        return (distance * ENERGY_PER_KM[terrain]) * (
            self._mass_kg / REFERENCE_MASS_KG
        )

    def calculate_energy(self, distance_km: float, terrain: str) -> float:
        """Возвращает расход энергии на поездку, не меняя состояние.

        Raises:
            TypeError, ValueError: неверные параметры.
            UnsupportedTerrainError: ``water`` или ``air``.
            RollingTerrainError: ``rock``/``sand`` в режиме ``roll``.
        """
        distance = self._checked_route(distance_km, terrain)
        return self._cost(distance, terrain)

    def move(self, distance_km: float, terrain: str) -> float:
        """Перемещает транспорт и возвращает время поездки в часах.

        Raises:
            TypeError, ValueError: неверные параметры.
            UnsupportedTerrainError: ``water`` или ``air``.
            RollingTerrainError: ``rock``/``sand`` в режиме ``roll``.
            InsufficientEnergyError: запас меньше расхода.
        """
        distance = self._checked_route(distance_km, terrain)
        cost = self._cost(distance, terrain)
        if self._energy < cost:
            raise InsufficientEnergyError("not enough energy to move")

        speed = (
            SPEED_PER_METER_OF_WHEEL[(self._mode, terrain)]
            * self._wheel_diameter_m
        )
        self._energy -= cost
        self._distance_km += distance
        return distance / speed

    # --- Панцирь (SPEC 3.4.3, 3.4.4) ---------------------------------------

    def fold_shell(self) -> None:
        """Сворачивает панцирь: ``crawl`` → ``roll`` за 10 ед. энергии.

        Raises:
            ShellStateError: панцирь уже свёрнут.
            InsufficientEnergyError: энергии меньше 10.
        """
        if self._mode == ROLL:
            raise ShellStateError("shell is already folded")
        if self._energy < FOLD_COST:
            raise InsufficientEnergyError("not enough energy to fold shell")
        self._energy -= FOLD_COST
        self._mode = ROLL

    def unfold_shell(self) -> None:
        """Раскрывает панцирь: ``roll`` → ``crawl`` за 5 ед. энергии.

        Raises:
            ShellStateError: панцирь уже раскрыт.
            InsufficientEnergyError: энергии меньше 5.
        """
        if self._mode == CRAWL:
            raise ShellStateError("shell is already unfolded")
        if self._energy < UNFOLD_COST:
            raise InsufficientEnergyError(
                "not enough energy to unfold shell"
            )
        self._energy -= UNFOLD_COST
        self._mode = CRAWL

    # --- Заправка и статус (SPEC 3.4.5, 3.4.6) -----------------------------

    def refuel(self, amount: float) -> None:
        """Заряжает аккумулятор, не выше 100.

        Raises:
            TypeError: ``amount`` не число.
            ValueError: ``amount`` неконечное или не больше нуля.
        """
        charge = _positive_number(amount, "amount")
        self._energy = min(MAX_ENERGY, self._energy + charge)

    def get_status(self) -> dict[str, str | float]:
        """Возвращает новый словарь-снимок всех публичных атрибутов."""
        return {
            "name": self._name,
            "mass_kg": self._mass_kg,
            "wheel_diameter_m": self._wheel_diameter_m,
            "energy": self._energy,
            "distance_km": self._distance_km,
            "mode": self._mode,
        }

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(name={self._name!r}, "
            f"energy={self._energy!r}, distance_km={self._distance_km!r}, "
            f"mode={self._mode!r})"
        )
