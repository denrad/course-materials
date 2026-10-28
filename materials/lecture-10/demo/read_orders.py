"""Требуется pandas. Запуск: python3 read_orders.py из каталога demo/."""
from pathlib import Path
import pandas as pd

orders = pd.read_csv(
    Path(__file__).with_name("orders.csv"),
    sep=";",
    dtype={"postal_code": "string"}
)
print(orders)
print(orders.groupby("city")["amount_rub"].sum())
