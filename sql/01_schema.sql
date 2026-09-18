-- Schema do banco de dados do projeto de análise de capacidade e demanda
-- em rotas de abastecimento (contexto PPCP / Material Handling).

DROP TABLE IF EXISTS demand;
DROP TABLE IF EXISTS part_numbers;
DROP TABLE IF EXISTS routes;

CREATE TABLE part_numbers (
    id          INTEGER PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    family      TEXT NOT NULL,
    weight_kg   REAL NOT NULL,
    length_mm   INTEGER NOT NULL,
    width_mm    INTEGER NOT NULL,
    height_mm   INTEGER NOT NULL
);

CREATE TABLE routes (
    id                   INTEGER PRIMARY KEY,
    name                 TEXT NOT NULL,
    region               TEXT NOT NULL,
    trailer_capacity_kg  REAL NOT NULL
);

CREATE TABLE demand (
    id              INTEGER PRIMARY KEY,
    part_number_id  INTEGER NOT NULL REFERENCES part_numbers(id),
    route_id        INTEGER NOT NULL REFERENCES routes(id),
    demand_date     DATE NOT NULL,
    quantity        INTEGER NOT NULL
);

CREATE INDEX idx_demand_route_date ON demand(route_id, demand_date);
CREATE INDEX idx_demand_part ON demand(part_number_id);
