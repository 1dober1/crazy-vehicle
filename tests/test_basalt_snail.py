"""Модульные проверки SPEC 0.3.0 в паттерне Arrange–Act–Assert."""

import io
import itertools
from contextlib import redirect_stdout

from tests.support import ContractTestCase


class BasaltSnailModuleTests(ContractTestCase):
    """Проверяет поведение класса и исключений через публичный контракт."""

    def test_TC_M_01_init_defaults(self) -> None:
        """TC_M_01: обязательные параметры и начальное состояние."""
        vehicle = self.vehicle_class("Улитка-1", 200.0)

        self.assert_state(self.public_state(vehicle), self.expected_state())

    def test_TC_M_02_init_explicit_parameters(self) -> None:
        """TC_M_02: явные параметры и нормализация числовых типов."""
        for keyword in (False, True):
            with self.subTest(keyword=keyword):
                if keyword:
                    vehicle = self.vehicle_class(
                        name="Тяжёлая", mass_kg=350,
                        wheel_diameter_m=2, energy=60,
                    )
                else:
                    vehicle = self.vehicle_class("Тяжёлая", 350, 2, 60)

                self.assert_state(
                    self.public_state(vehicle),
                    self.expected_state(
                        name="Тяжёлая", mass_kg=350.0,
                        wheel_diameter_m=2.0, energy=60.0,
                    ),
                )

    def test_TC_M_03_init_boundaries(self) -> None:
        """TC_M_03: все сочетания включённых границ конструктора."""
        combinations = itertools.product(
            (100.0, 500.0), (0.5, 2.0), (0.0, 100.0)
        )
        for mass, diameter, energy in combinations:
            with self.subTest(mass=mass, diameter=diameter, energy=energy):
                vehicle = self.vehicle_class("Улитка-1", mass, diameter, energy)

                self.assert_state(
                    self.public_state(vehicle),
                    self.expected_state(
                        mass_kg=mass, wheel_diameter_m=diameter, energy=energy
                    ),
                )

    def test_TC_M_04_name_normalization(self) -> None:
        """TC_M_04: удаляются только внешние пробельные символы имени."""
        vehicle = self.make_vehicle(name="  Каменная  Улитка \t\n")

        self.assert_state(
            self.public_state(vehicle),
            self.expected_state(name="Каменная  Улитка"),
        )

    def test_TC_M_05_init_invalid_types(self) -> None:
        """TC_M_05: неверные типы конструктора, включая bool вместо числа."""
        variants = {
            "name": (None, 10, True, []),
            "mass_kg": ("200", None, True, False, []),
            "wheel_diameter_m": ("200", None, True, False, []),
            "energy": ("200", None, True, False, []),
        }
        for parameter, values in variants.items():
            message = (
                "name must be a string" if parameter == "name"
                else f"{parameter} must be a number"
            )
            for value in values:
                with self.subTest(parameter=parameter, value=value):
                    self.assert_error(
                        TypeError, message,
                        lambda: self.make_vehicle(**{parameter: value}),
                    )

    def test_TC_M_06_init_invalid_values(self) -> None:
        """TC_M_06: пустые имена, выход за границы и неконечные числа."""
        nonfinite = (float("nan"), float("inf"), float("-inf"))
        variants = {
            "name": (("", " \t\n"), "name must not be empty"),
            "mass_kg": (
                (99.999, 500.001) + nonfinite,
                "mass_kg must be finite and between 100 and 500",
            ),
            "wheel_diameter_m": (
                (0.499, 2.001) + nonfinite,
                "wheel_diameter_m must be finite and between 0.5 and 2",
            ),
            "energy": (
                (-0.001, 100.001) + nonfinite,
                "energy must be finite and between 0 and 100",
            ),
        }
        for parameter, (values, message) in variants.items():
            for value in values:
                with self.subTest(parameter=parameter, value=value):
                    self.assert_error(
                        ValueError, message,
                        lambda: self.make_vehicle(**{parameter: value}),
                    )

    def test_TC_M_07_attributes_are_read_only(self) -> None:
        """TC_M_07: присваивание и удаление атрибутов запрещены и атомарны."""
        replacements = {
            "name": "Другое имя", "mass_kg": 300.0,
            "wheel_diameter_m": 2.0, "energy": 50.0,
            "distance_km": 10.0, "mode": "roll",
        }
        for (attribute, replacement), operation in itertools.product(
            replacements.items(), ("assign", "delete")
        ):
            with self.subTest(attribute=attribute, operation=operation):
                vehicle = self.make_vehicle()
                before = self.public_state(vehicle)

                with self.assertRaises(AttributeError):
                    if operation == "assign":
                        setattr(vehicle, attribute, replacement)
                    else:
                        delattr(vehicle, attribute)

                self.assert_state(self.public_state(vehicle), before, exact=True)

    def test_TC_M_08_init_error_precedence(self) -> None:
        """TC_M_08: тип и значение каждого параметра проверяются по порядку."""
        cases = (
            ((None, -1, -1, -1), TypeError, "name must be a string"),
            (("", "bad", -1, -1), ValueError, "name must not be empty"),
            (("ok", "bad", -1, -1), TypeError, "mass_kg must be a number"),
            (("ok", -1, "bad", -1), ValueError,
             "mass_kg must be finite and between 100 and 500"),
            (("ok", 200, "bad", -1), TypeError,
             "wheel_diameter_m must be a number"),
            (("ok", 200, -1, "bad"), ValueError,
             "wheel_diameter_m must be finite and between 0.5 and 2"),
        )
        for arguments, error_class, message in cases:
            with self.subTest(arguments=arguments):
                self.assert_error(
                    error_class, message,
                    lambda: self.vehicle_class(*arguments),
                )

    def test_TC_M_09_estimate_crawl_costs(self) -> None:
        """TC_M_09: расход зависит от грунта и массы, расчёт не мутирует."""
        costs = {
            100.0: (5.0, 10.0, 15.0),
            200.0: (10.0, 20.0, 30.0),
            500.0: (25.0, 50.0, 75.0),
        }
        for mass, expected_costs in costs.items():
            for terrain, expected_cost in zip(
                ("road", "rock", "sand"), expected_costs
            ):
                with self.subTest(mass=mass, terrain=terrain):
                    vehicle = self.make_vehicle(mass_kg=mass)
                    before = self.public_state(vehicle)

                    cost = vehicle.calculate_energy(2.0, terrain)

                    self.assert_result(cost, expected_cost)
                    self.assert_state(self.public_state(vehicle), before)

        for keyword in (False, True):
            with self.subTest(fractional=True, keyword=keyword):
                vehicle = self.make_vehicle(mass_kg=150.5)
                before = self.public_state(vehicle)

                if keyword:
                    cost = vehicle.calculate_energy(distance_km=0.3, terrain="sand")
                else:
                    cost = vehicle.calculate_energy(0.3, "sand")

                self.assertIs(type(cost), float)
                self.assertEqual(cost, 3.3862499999999995)
                self.assert_state(self.public_state(vehicle), before)

    def test_TC_M_10_estimate_roll_cost(self) -> None:
        """TC_M_10: сворачивание и диаметр не меняют формулу расхода."""
        vehicle = self.make_vehicle(mass_kg=400.0, wheel_diameter_m=2.0)
        vehicle.fold_shell()
        before = self.public_state(vehicle)

        cost = vehicle.calculate_energy(3, "road")

        self.assert_result(cost, 30.0)
        self.assert_state(self.public_state(vehicle), before)

    def test_TC_M_11_estimate_without_energy(self) -> None:
        """TC_M_11: оценка доступна с нулевым зарядом в обоих режимах."""
        for mode in ("crawl", "roll"):
            with self.subTest(mode=mode):
                vehicle = self.make_vehicle(energy=0.0 if mode == "crawl" else 10.0)
                if mode == "roll":
                    vehicle.fold_shell()
                before = self.public_state(vehicle)

                cost = vehicle.calculate_energy(1, "road")

                self.assert_result(cost, 5.0)
                self.assert_state(self.public_state(vehicle), before)

    def test_TC_M_12_invalid_distance(self) -> None:
        """TC_M_12: оба метода отвергают неверные типы и значения дистанции."""
        groups = (
            (("1", None, True, False, []), TypeError,
             "distance_km must be a number"),
            ((0, -1, float("nan"), float("inf"), float("-inf")), ValueError,
             "distance_km must be finite and positive"),
        )
        for method_name in ("move", "calculate_energy"):
            for values, error_class, message in groups:
                for value in values:
                    with self.subTest(method=method_name, value=value):
                        vehicle = self.make_vehicle()
                        action = getattr(vehicle, method_name)

                        self.assert_atomic_error(
                            vehicle, error_class, message,
                            lambda: action(value, "road"),
                        )

    def test_TC_M_13_invalid_terrain(self) -> None:
        """TC_M_13: тип, набор строк, регистр и пробелы terrain проверяются."""
        groups = (
            ((None, 1, True, []), TypeError, "terrain must be a string"),
            (("", "mud", "ROAD", " road "), ValueError, "unknown terrain"),
        )
        for method_name in ("move", "calculate_energy"):
            for values, error_class, message in groups:
                for value in values:
                    with self.subTest(method=method_name, value=value):
                        vehicle = self.make_vehicle()
                        action = getattr(vehicle, method_name)

                        self.assert_atomic_error(
                            vehicle, error_class, message,
                            lambda: action(1, value),
                        )

    def test_TC_M_14_non_land_terrain(self) -> None:
        """TC_M_14: вода и воздух запрещены для расчёта и движения."""
        variants = itertools.product(
            ("crawl", "roll"), ("move", "calculate_energy"), ("water", "air")
        )
        for mode, method_name, terrain in variants:
            with self.subTest(mode=mode, method=method_name, terrain=terrain):
                vehicle = self.make_vehicle()
                if mode == "roll":
                    vehicle.fold_shell()
                action = getattr(vehicle, method_name)

                self.assert_atomic_error(
                    vehicle, self.contract.UnsupportedTerrainError,
                    "basalt snail can only travel on land",
                    lambda: action(1, terrain),
                )

    def test_TC_M_15_rolling_terrain_restriction(self) -> None:
        """TC_M_15: свёрнутый транспорт не движется по камням и песку."""
        for method_name, terrain in itertools.product(
            ("move", "calculate_energy"), ("rock", "sand")
        ):
            with self.subTest(method=method_name, terrain=terrain):
                vehicle = self.make_vehicle()
                vehicle.fold_shell()
                action = getattr(vehicle, method_name)

                self.assert_atomic_error(
                    vehicle, self.contract.RollingTerrainError,
                    "rolling is only allowed on road",
                    lambda: action(1, terrain),
                )

    def test_TC_M_16_move_crawl(self) -> None:
        """TC_M_16: движение по каждому грунту меняет только заряд и путь."""
        cases = (
            ("road", 0.2, 90.0), ("rock", 0.4, 80.0), ("sand", 1.0, 70.0)
        )
        for (terrain, duration, energy), keyword in itertools.product(
            cases, (False, True)
        ):
            with self.subTest(terrain=terrain, keyword=keyword):
                vehicle = self.make_vehicle()

                if keyword:
                    result = vehicle.move(distance_km=2, terrain=terrain)
                else:
                    result = vehicle.move(2, terrain)

                self.assert_result(result, duration)
                self.assert_state(
                    self.public_state(vehicle),
                    self.expected_state(energy=energy, distance_km=2.0),
                )

    def test_TC_M_17_move_roll(self) -> None:
        """TC_M_17: свёрнутый панцирь ускоряет движение по дороге."""
        vehicle = self.make_vehicle()
        vehicle.fold_shell()

        result = vehicle.move(2, "road")

        self.assert_result(result, 0.05)
        self.assert_state(
            self.public_state(vehicle),
            self.expected_state(energy=80.0, distance_km=2.0, mode="roll"),
        )

    def test_TC_M_18_move_exact_energy(self) -> None:
        """TC_M_18: ровно достаточная энергия допускает нулевой остаток."""
        cases = (
            ("road", 5.0, 0.1), ("rock", 10.0, 0.2), ("sand", 15.0, 0.5)
        )
        for terrain, initial_energy, duration in cases:
            with self.subTest(terrain=terrain):
                vehicle = self.make_vehicle(energy=initial_energy)

                result = vehicle.move(1, terrain)

                self.assert_result(result, duration)
                self.assert_state(
                    self.public_state(vehicle),
                    self.expected_state(energy=0.0, distance_km=1.0),
                )
                self.assertEqual(vehicle.energy, 0.0)

        for initial_energy, expected_energy in (
            (3.3862499999999995, 0.0),
            (3.38625, 4.440892098500626e-16),
        ):
            with self.subTest(fractional_energy=initial_energy):
                vehicle = self.make_vehicle(mass_kg=150.5, energy=initial_energy)

                result = vehicle.move(0.3, "sand")

                self.assert_result(result, 0.15)
                self.assert_state(
                    self.public_state(vehicle),
                    self.expected_state(
                        mass_kg=150.5, energy=expected_energy, distance_km=0.3,
                    ),
                )
                self.assertEqual(vehicle.energy, expected_energy)

        with self.subTest(fractional_energy=3.386249999999999):
            vehicle = self.make_vehicle(mass_kg=150.5, energy=3.386249999999999)
            before = self.public_state(vehicle)

            self.assert_atomic_error(
                vehicle, self.contract.InsufficientEnergyError,
                "not enough energy to move", lambda: vehicle.move(0.3, "sand"),
            )

            self.assertEqual(self.public_state(vehicle), before)

    def test_TC_M_19_insufficient_energy(self) -> None:
        """TC_M_19: движение и оба переключения атомарны при нехватке заряда."""
        cases = (
            ("move", 4.0, (1, "road"), "not enough energy to move"),
            ("fold_shell", 9.999, (), "not enough energy to fold shell"),
            ("unfold_shell", 14.999, (), "not enough energy to unfold shell"),
        )
        for method_name, energy, arguments, message in cases:
            with self.subTest(method=method_name):
                vehicle = self.make_vehicle(energy=energy)
                if method_name == "unfold_shell":
                    vehicle.fold_shell()
                action = getattr(vehicle, method_name)

                self.assert_atomic_error(
                    vehicle, self.contract.InsufficientEnergyError,
                    message, lambda: action(*arguments),
                )

    def test_TC_M_20_fold_shell(self) -> None:
        """TC_M_20: сворачивание расходует 10, меняет режим и возвращает None."""
        vehicle = self.make_vehicle()

        result = vehicle.fold_shell()

        self.assertIsNone(result)
        self.assert_state(
            self.public_state(vehicle),
            self.expected_state(energy=90.0, mode="roll"),
        )

    def test_TC_M_21_unfold_shell(self) -> None:
        """TC_M_21: раскрытие расходует 5, меняет режим и возвращает None."""
        vehicle = self.make_vehicle()
        vehicle.fold_shell()

        result = vehicle.unfold_shell()

        self.assertIsNone(result)
        self.assert_state(
            self.public_state(vehicle), self.expected_state(energy=85.0)
        )

    def test_TC_M_22_repeated_shell_commands(self) -> None:
        """TC_M_22: повтор команды вызывает ошибку состояния раньше энергии."""
        cases = (
            ("fold_shell", 10.0, "shell is already folded"),
            ("unfold_shell", 0.0, "shell is already unfolded"),
        )
        for method_name, energy, message in cases:
            with self.subTest(method=method_name):
                vehicle = self.make_vehicle(energy=energy)
                if method_name == "fold_shell":
                    vehicle.fold_shell()
                action = getattr(vehicle, method_name)

                self.assert_atomic_error(
                    vehicle, self.contract.ShellStateError, message, action
                )

    def test_TC_M_23_action_error_precedence(self) -> None:
        """TC_M_23: параметры, стихия и режим первичны относительно энергии."""
        cases = (
            ("bad", "water", TypeError, "distance_km must be a number"),
            (0, [], ValueError, "distance_km must be finite and positive"),
            (1, [], TypeError, "terrain must be a string"),
            (1, "mud", ValueError, "unknown terrain"),
            (1, "water", self.contract.UnsupportedTerrainError,
             "basalt snail can only travel on land"),
            (1, "rock", self.contract.RollingTerrainError,
             "rolling is only allowed on road"),
        )
        for method_name in ("move", "calculate_energy"):
            for distance, terrain, error_class, message in cases:
                with self.subTest(
                    method=method_name, distance=distance, terrain=terrain
                ):
                    vehicle = self.make_vehicle(energy=10.0)
                    vehicle.fold_shell()
                    action = getattr(vehicle, method_name)

                    self.assert_atomic_error(
                        vehicle, error_class, message,
                        lambda: action(distance, terrain),
                    )
        vehicle = self.make_vehicle(energy=10.0)
        vehicle.fold_shell()

        self.assert_atomic_error(
            vehicle, self.contract.InsufficientEnergyError,
            "not enough energy to move", lambda: vehicle.move(1, "road"),
        )

    def test_TC_M_24_refuel(self) -> None:
        """TC_M_24: целая и дробная зарядка сохраняют путь и режим."""
        for keyword in (False, True):
            with self.subTest(keyword=keyword):
                vehicle = self.make_vehicle(energy=60.0)
                vehicle.fold_shell()
                vehicle.move(1, "road")

                if keyword:
                    result = vehicle.refuel(amount=25)
                else:
                    result = vehicle.refuel(25)

                self.assertIsNone(result)
                self.assert_state(
                    self.public_state(vehicle),
                    self.expected_state(energy=70.0, distance_km=1.0, mode="roll"),
                )

        for keyword in (False, True):
            with self.subTest(amount=0.25, keyword=keyword):
                vehicle = self.make_vehicle(energy=60.0)

                if keyword:
                    result = vehicle.refuel(amount=0.25)
                else:
                    result = vehicle.refuel(0.25)

                self.assertIsNone(result)
                self.assert_state(
                    self.public_state(vehicle),
                    self.expected_state(energy=60.25),
                )
                self.assertEqual(vehicle.energy, 60.25)

    def test_TC_M_25_refuel_cap(self) -> None:
        """TC_M_25: лишний заряд отбрасывается, полный аккумулятор допустим."""
        for energy, amount in ((50.0, 1000), (100.0, 1)):
            with self.subTest(energy=energy, amount=amount):
                vehicle = self.make_vehicle(energy=energy)

                result = vehicle.refuel(amount)

                self.assertIsNone(result)
                self.assert_state(self.public_state(vehicle), self.expected_state())

    def test_TC_M_26_refuel_invalid_types(self) -> None:
        """TC_M_26: нечисловое количество заряда и bool запрещены."""
        for amount in ("10", None, True, False, []):
            with self.subTest(amount=amount):
                vehicle = self.make_vehicle()

                self.assert_atomic_error(
                    vehicle, TypeError, "amount must be a number",
                    lambda: vehicle.refuel(amount),
                )

    def test_TC_M_27_refuel_invalid_values(self) -> None:
        """TC_M_27: заряд должен быть конечным и строго положительным."""
        for amount in (0, -1, float("nan"), float("inf"), float("-inf")):
            with self.subTest(amount=amount):
                vehicle = self.make_vehicle()

                self.assert_atomic_error(
                    vehicle, ValueError, "amount must be finite and positive",
                    lambda: vehicle.refuel(amount),
                )

    def test_TC_M_28_status_snapshot(self) -> None:
        """TC_M_28: полный статус является независимым снимком без вывода."""
        vehicle = self.make_vehicle(energy=80.0)
        output = io.StringIO()
        before = self.public_state(vehicle)

        with redirect_stdout(output):
            first_snapshot = vehicle.get_status()
            second_snapshot = vehicle.get_status()

        self.assertEqual(output.getvalue(), "")
        self.assertIsNot(first_snapshot, second_snapshot)
        self.assert_state(first_snapshot, self.expected_state(energy=80.0))
        self.assert_state(second_snapshot, self.expected_state(energy=80.0))
        self.assert_state(self.public_state(vehicle), before)

        vehicle.refuel(5)

        self.assert_state(first_snapshot, self.expected_state(energy=80.0))
        self.assert_state(second_snapshot, self.expected_state(energy=80.0))
        first_snapshot["energy"] = 999.0
        first_snapshot["mode"] = "invalid"

        self.assert_state(
            self.public_state(vehicle), self.expected_state(energy=85.0)
        )

    def test_TC_M_29_wheel_speed_boundaries(self) -> None:
        """TC_M_29: диаметр на обеих границах определяет скорость, но не расход."""
        cases = {
            0.5: (("crawl", "road", 0.2, 95.0),
                  ("crawl", "rock", 0.4, 90.0),
                  ("crawl", "sand", 1.0, 85.0),
                  ("roll", "road", 0.05, 85.0)),
            2.0: (("crawl", "road", 0.05, 95.0),
                  ("crawl", "rock", 0.1, 90.0),
                  ("crawl", "sand", 0.25, 85.0),
                  ("roll", "road", 0.0125, 85.0)),
        }
        for diameter, variants in cases.items():
            for mode, terrain, duration, energy in variants:
                with self.subTest(diameter=diameter, mode=mode, terrain=terrain):
                    vehicle = self.make_vehicle(wheel_diameter_m=diameter)
                    if mode == "roll":
                        vehicle.fold_shell()

                    result = vehicle.move(1, terrain)

                    self.assert_result(result, duration)
                    self.assert_state(
                        self.public_state(vehicle),
                        self.expected_state(
                            energy=energy, distance_km=1.0, mode=mode,
                            wheel_diameter_m=diameter,
                        ),
                    )

    def test_TC_M_30_shell_exact_energy(self) -> None:
        """TC_M_30: ровно достаточный заряд разрешает оба переключения."""
        for method_name, energy, expected_mode in (
            ("fold_shell", 10.0, "roll"), ("unfold_shell", 15.0, "crawl")
        ):
            with self.subTest(method=method_name):
                vehicle = self.make_vehicle(energy=energy)
                if method_name == "unfold_shell":
                    vehicle.fold_shell()

                result = getattr(vehicle, method_name)()

                self.assertIsNone(result)
                self.assert_state(
                    self.public_state(vehicle),
                    self.expected_state(energy=0.0, mode=expected_mode),
                )

    def test_TC_M_31_exception_hierarchy(self) -> None:
        """TC_M_31: экспортируется собственная иерархия доменных исключений."""
        hierarchy = (
            ("CrazyVehicleError", Exception),
            ("BasaltSnailError", self.contract.CrazyVehicleError),
            ("UnsupportedTerrainError", self.contract.BasaltSnailError),
            ("RollingTerrainError", self.contract.BasaltSnailError),
            ("InsufficientEnergyError", self.contract.BasaltSnailError),
            ("ShellStateError", self.contract.BasaltSnailError),
        )
        for class_name, parent in hierarchy:
            with self.subTest(class_name=class_name):
                error_class = getattr(self.contract, class_name)

                self.assertEqual(error_class.__bases__, (parent,))
                for standard_error in (RuntimeError, ValueError, TypeError):
                    self.assertFalse(issubclass(error_class, standard_error))

    def test_TC_M_32_independent_vehicles(self) -> None:
        """TC_M_32: одинаковые имена допустимы, состояние объектов независимо."""
        first_vehicle = self.make_vehicle()
        second_vehicle = self.make_vehicle()

        first_vehicle.fold_shell()

        self.assert_state(
            self.public_state(first_vehicle),
            self.expected_state(energy=90.0, mode="roll"),
        )
        self.assert_state(self.public_state(second_vehicle), self.expected_state())
