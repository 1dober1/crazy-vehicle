# Проверка после двух ревью

Дата: **21.10.2026**. Версия SPEC: **0.3.0**.
Этап: ТЗ и тесты до реализации, до заморозки.  
Связанные артефакты: [отзыв Филиппова](REVIEW_basalt_snail.md), [отзыв Хвальчева](REVIEW_basalt_snail_Khvalchev.md), [ответы](RESPONSES.md), [журнал](CHANGELOG.md).

## Выполненные проверки

1. Разбор всех пяти файлов `tests/*.py` через `ast.parse`: без синтаксических ошибок.
2. Обнаружение тестов через `unittest`: 40 методов, 32 модульных и 8 сценарных. Совпадение всех 40 ID в TCS, именах методов, docstring и трассируемости проверено.
3. Полный прогон: 40 запущенных тестов, 0 failures, **40 errors**. Каждая ошибка — `ModuleNotFoundError: No module named 'basalt_snail'` в подготовке теста. Пропущенных тестов нет. До реализации это ожидаемый красный прогон, предусмотренный заданием. Успешное выполнение проверок поведения транспорта пока не подтверждено.
4. Числовой пример R-2 пересчитан непосредственно в Python: исходная группировка даёт `3.3862499999999995`, перегруппировка — `3.38625`, остаток от запаса `3.38625` — `4.440892098500626e-16`. Регрессионные варианты используют точное сравнение, чтобы обычный допуск в 7 знаков не скрывал расхождение.

5. Отдельная проверка `assert_atomic_error` и `assert_pilot_error` на тестовых объектах: оба принимают неизменное состояние и отклоняют изменение энергии на один шаг `float`, изменение пути на `1e-10` и замену типа энергии `float` на `int`. Всего 8 вариантов: 2 неизменных состояния приняты, 6 мутаций обнаружены. Реализация транспорта для этой проверки не требуется.
6. Расширены `TC_M_07` (присваивание и удаление всех шести атрибутов) и `TC_M_24` (дробная заправка `60.0 + 0.25 = 60.25`, оба способа передачи аргумента). Исполнение этих кейсов на реальном транспорте ожидает реализацию.
7. Исходный файл отзыва Хвальчева сохранён без изменений: Git blob SHA-1 `5734a57f6bd544bcf26c8458bf73c06d33196072` совпадает с файлом из PR № 2.

## Как повторить

Из корня репозитория, Python 3.10+:

```bash
python3 - <<'PY'
import ast
from pathlib import Path
import unittest

files = sorted(Path("tests").glob("*.py"))
for path in files:
    ast.parse(path.read_text(), filename=str(path))
print("AST: OK", len(files))
suite = unittest.defaultTestLoader.discover("tests", top_level_dir=".")
print("Discovered tests:", suite.countTestCases())
print("Cost:", repr((0.3 * 15.0) * (150.5 / 200.0)))
print("Reassociated cost:", repr(0.3 * 15.0 * 150.5 / 200.0))
print("Remainder:", repr(3.38625 - (0.3 * 15.0) * (150.5 / 200.0)))
PY
python3 -m unittest discover -s tests -t . -v
```

После добавления разработчиком `basalt_snail.py` полный прогон нужно повторить. Падения классифицируются как ошибка кода, теста или ТЗ и оформляются на этапе приёмки в `ACCEPTANCE.md` и `FIXES.md` с записью об изменениях в `CHANGELOG.md`. Эти этапы пока не завершены.

## Как повторить проверку помощников атомарности

Проверка ниже не запускает `setUp` контрактных тестов и не подставляет реализацию транспорта:

```bash
python3 - <<'PY'
import math
from types import SimpleNamespace
from tests.support import ContractTestCase
from tests.test_scenarios import BasaltSnailScenarioTests

accepted = rejected = 0
for kind in ("module", "pilot"):
    for mutation in ("none", "energy", "distance_km", "type"):
        check = (ContractTestCase() if kind == "module" else
                 BasaltSnailScenarioTests("test_TC_S_01_mixed_terrain_delivery"))
        vehicle = SimpleNamespace(**check.expected_state(energy=60.0))
        pilot = SimpleNamespace(status=lambda: check.public_state(vehicle))

        def action():
            if mutation == "energy":
                vehicle.energy = math.nextafter(vehicle.energy, math.inf)
            if mutation == "distance_km":
                vehicle.distance_km = 1e-10
            if mutation == "type":
                vehicle.energy = 60
            raise ValueError("expected")

        try:
            if kind == "module":
                check.assert_atomic_error(vehicle, ValueError, "expected", action)
            else:
                check.assert_pilot_error(pilot, ValueError, "expected", action)
        except AssertionError:
            assert mutation != "none", (kind, mutation)
            rejected += 1
        else:
            assert mutation == "none", (kind, mutation)
            accepted += 1
assert (accepted, rejected) == (2, 6)
print("Unchanged states accepted:", accepted, "Mutations detected:", rejected)
PY
```
