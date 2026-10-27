# Безумный транспорт: "Базальтовая Улитка"

Автор ТЗ и тестов: **Цыганков Александр Дмитриевич**, **БСБО-16-23**. Стихия: **земля**.

"Базальтовая Улитка" — одноместный наземный транспорт с каменными колёсами и сворачивающимся панцирем. В раскрытом состоянии он преодолевает камни и песок; в свёрнутом быстро катится по дороге.

![Базальтовая Улитка](assets/basalt-snail.png)

## Структура репозитория

```text
SPEC.md                      — публичный контракт транспорта
TEST_CASES.md                — входные данные и ожидаемые результаты тестов
tests/
├── __init__.py
├── test_basalt_snail.py      — модульные тесты
├── test_scenarios.py         — сценарные тесты
├── pilot.py                 — тестовый пилот
└── support.py               — общие проверки контракта
assets/
└── basalt-snail.png          — изображение транспорта
```

Модуль реализации: `basalt_snail.py` в корне проекта. Класс `BasaltSnail` и исключения определены в [SPEC.md](SPEC.md). Тесты проверяют публичный интерфейс; `Pilot` используется только в сценарных тестах.

## Ревью и история работы

ТЗ и тесты зафиксированы в версии **1.0.0** от **21.10.2026**.

Изменения контракта оформляются в `CHANGELOG.md` с регрессионными тестами. Существенные изменения ТЗ проходят повторное ревью.

- [Исходный отзыв Филиппова](REVIEW_basalt_snail.md), [PR № 1](https://github.com/1dober1/crazy-vehicle/pull/1).
- [Исходный отзыв Хвальчева](REVIEW_basalt_snail_Khvalchev.md), [PR № 2](https://github.com/1dober1/crazy-vehicle/pull/2).
- [Ответы автора по каждому замечанию](RESPONSES.md).
- [Журнал изменений](CHANGELOG.md).
- [Результаты проверки и команды воспроизведения](VALIDATION.md).
- [Приёмка реализации](ACCEPTANCE.md).
- [Журнал исправлений](FIXES.md).

## Запуск тестов

Python **3.10+**, без сторонних зависимостей. Из корня проекта:

```bash
python3 -m unittest discover -s tests -t . -v
```

## Реализация (роль D)

Разработчик: **Крашенинников Матвей Вячеславович**, **БСБО-16-23**.

Модуль `basalt_snail.py` в корне проекта реализует контракт SPEC **1.0.0**: класс `BasaltSnail` и исключения раздела 6. Сторонних зависимостей нет, требуется Python **3.10+**.

```python
from basalt_snail import BasaltSnail, RollingTerrainError

snail = BasaltSnail("Улитка-1", mass_kg=200.0)
snail.move(2.0, "road")      # 0.2 ч, энергия 90.0
snail.fold_shell()           # режим roll, энергия 80.0
snail.move(1.0, "road")      # 0.025 ч, энергия 75.0
try:
    snail.move(1.0, "rock")
except RollingTerrainError as error:
    print(error)             # rolling is only allowed on road
print(snail.get_status())
```

Проверка из корня проекта:

```bash
python3 -m unittest discover -s tests -t . -v   # 40 тестов, OK
```

Вопросы разработчика к ТЗ и тестам — в [BUGREPORT.md](BUGREPORT.md).

## Защита

- [Сценарий демонстрации](DEMO.md).
- [Материал выступления](PRESENTATION.md).
- [Рефлексия автора ТЗ](REFLECTION.md).

Запуск демонстрации из корня проекта:

```bash
python3 demo.py
```
