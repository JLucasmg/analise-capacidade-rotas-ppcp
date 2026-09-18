# -*- coding: utf-8 -*-
"""
Gera dados 100% sintéticos para o projeto de análise de capacidade e demanda
em rotas de abastecimento (contexto PPCP / Material Handling).

Nenhum valor aqui vem de dados reais de qualquer empresa. Os números foram
desenhados apenas para reproduzir, em escala e formato, o tipo de base com
que um analista de PPCP trabalha no dia a dia (peças, rotas, demanda,
capacidade), permitindo praticar modelagem e SQL sobre um cenário realista.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------
# 1) PART NUMBERS
# ---------------------------------------------------------------
N_PARTS = 300
FAMILIES = ["Chassi", "Motor", "Interior", "Elétrico", "Suspensão"]

family = RNG.choice(FAMILIES, size=N_PARTS, p=[0.25, 0.2, 0.25, 0.15, 0.15])

# peso segue distribuição assimétrica (poucas peças muito pesadas) -> gamma
weight_kg = RNG.gamma(shape=2.0, scale=2.3, size=N_PARTS)
weight_kg = np.round(np.clip(weight_kg, 0.05, None), 2)

length_mm = RNG.integers(40, 1200, size=N_PARTS)
width_mm = RNG.integers(40, 800, size=N_PARTS)
height_mm = RNG.integers(30, 600, size=N_PARTS)

part_numbers = pd.DataFrame({
    "id": np.arange(1, N_PARTS + 1),
    "code": [f"PN-{1000 + i}" for i in range(N_PARTS)],
    "family": family,
    "weight_kg": weight_kg,
    "length_mm": length_mm,
    "width_mm": width_mm,
    "height_mm": height_mm,
})
part_numbers.to_csv(OUT / "part_numbers.csv", index=False)

# ---------------------------------------------------------------
# 2) ROTAS
# ---------------------------------------------------------------
routes = pd.DataFrame({
    "id": [1, 2, 3, 4],
    "name": ["Rota Norte", "Rota Sul", "Rota Leste", "Rota Oeste"],
    "region": ["Norte", "Sul", "Leste", "Oeste"],
    "trailer_capacity_kg": [850.0, 1200.0, 700.0, 950.0],
})
routes.to_csv(OUT / "routes.csv", index=False)

# ---------------------------------------------------------------
# 3) DEMANDA (180 dias, cada rota atende um subconjunto de peças)
# ---------------------------------------------------------------
N_DAYS = 180
dates = pd.date_range("2026-01-01", periods=N_DAYS, freq="D")

# cada rota "pertence" a um subconjunto de peças (mistura de famílias)
route_part_pool = {
    1: part_numbers.sample(90, random_state=1)["id"].tolist(),
    2: part_numbers.sample(110, random_state=2)["id"].tolist(),
    3: part_numbers.sample(70, random_state=3)["id"].tolist(),
    4: part_numbers.sample(100, random_state=4)["id"].tolist(),
}

rows = []
row_id = 1
for route_id, pool in route_part_pool.items():
    # cada rota tem um "nível de atividade" diferente
    base_lambda = {1: 3.2, 2: 5.0, 3: 2.1, 4: 3.8}[route_id]
    for date in dates:
        # sazonalidade: menor atividade em finais de semana + ruído
        weekday_factor = 0.4 if date.weekday() >= 5 else 1.0
        # picos ocasionais (ex.: reposição semanal concentrada)
        spike = 1.8 if RNG.random() < 0.05 else 1.0

        n_parts_today = RNG.integers(15, min(40, len(pool)))
        parts_today = RNG.choice(pool, size=n_parts_today, replace=False)

        for pn_id in parts_today:
            qty = RNG.poisson(base_lambda * weekday_factor * spike)
            if qty <= 0:
                continue
            rows.append((row_id, pn_id, route_id, date.date().isoformat(), int(qty)))
            row_id += 1

demand = pd.DataFrame(rows, columns=[
    "id", "part_number_id", "route_id", "demand_date", "quantity"
])
demand.to_csv(OUT / "demand.csv", index=False)

print(f"part_numbers.csv: {len(part_numbers)} linhas")
print(f"routes.csv:       {len(routes)} linhas")
print(f"demand.csv:       {len(demand)} linhas")
