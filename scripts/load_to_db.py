# -*- coding: utf-8 -*-
"""Cria o banco SQLite a partir do schema e carrega os CSVs sintéticos."""

import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "ppcp.db"
RAW = ROOT / "data" / "raw"
SCHEMA = ROOT / "sql" / "01_schema.sql"

if DB_PATH.exists():
    DB_PATH.unlink()

conn = sqlite3.connect(DB_PATH)
conn.executescript(SCHEMA.read_text(encoding="utf-8"))

pd.read_csv(RAW / "part_numbers.csv").to_sql("part_numbers", conn, if_exists="append", index=False)
pd.read_csv(RAW / "routes.csv").to_sql("routes", conn, if_exists="append", index=False)
pd.read_csv(RAW / "demand.csv").to_sql("demand", conn, if_exists="append", index=False)

conn.commit()

counts = {
    t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    for t in ["part_numbers", "routes", "demand"]
}
print(f"Banco criado em: {DB_PATH}")
print("Linhas carregadas:", counts)

conn.close()
