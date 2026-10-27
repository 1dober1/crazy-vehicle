"""Демонстрация «Базальтовой Улитки» для защиты.

Запуск из корня репозитория: python3 demo.py
"""

from basalt_snail import BasaltSnail, RollingTerrainError, InsufficientEnergyError

u = BasaltSnail("Улитка-1", mass_kg=200.0)
print("Дорога 2 км, часов:", u.move(2.0, "road"))
u.fold_shell()
print("Свернулась:", u.get_status())
print("Дорога 1 км в roll, часов:", u.move(1.0, "road"))
try:
    u.move(1.0, "rock")
except RollingTerrainError as e:
    print("Камни в roll:", type(e).__name__, "-", e)
u.unfold_shell()
print("Камни 2 км, часов:", u.move(2.0, "rock"))
print("Статус:", u.get_status())

t = BasaltSnail("Тонкая", mass_kg=150.5, energy=3.38625)
print("Расход 0.3 км песка:", t.calculate_energy(0.3, "sand"))
t.move(0.3, "sand")
print("Остаток энергии:", t.energy)
try:
    t.fold_shell()
except InsufficientEnergyError as e:
    print("Сворачивание:", type(e).__name__, "-", e)
