# Análise de Capacidade e Demanda em Rotas de Abastecimento

Projeto de modelagem de dados e SQL aplicado a um cenário de **Planejamento e
Controle da Produção (PPCP)**: gestão de rotas de abastecimento interno,
onde peças (Part Numbers) de diferentes famílias são transportadas até a
linha de produção com um limite de capacidade de peso por rota.

> **Nota sobre os dados:** todos os dados usados aqui são **sintéticos**,
> gerados por script (`scripts/generate_synthetic_data.py`). Nenhuma
> informação real de qualquer empresa foi utilizada — apenas a estrutura e a
> escala do problema foram inspiradas em rotinas reais de PPCP / Material
> Handling em ambiente industrial.

## Perguntas de negócio

O projeto foi desenhado para responder:

1. Qual rota tem o maior volume de demanda nos últimos 6 meses?
2. Quais Part Numbers concentram o maior peso total transportado (lógica 80/20)?
3. Qual é o percentil 95 (P95) da demanda diária por rota — ou seja, para
   qual volume a capacidade deveria ser dimensionada?
4. Em quais dias e rotas o peso transportado ultrapassou a capacidade da
   carretinha?
5. Qual rota tem a maior variabilidade (desvio padrão) de demanda diária,
   e portanto exige mais atenção no planejamento?

## Modelo de dados

Três tabelas relacionais:

```
part_numbers (id, code, family, weight_kg, length_mm, width_mm, height_mm)
routes       (id, name, region, trailer_capacity_kg)
demand       (id, part_number_id → part_numbers, route_id → routes,
              demand_date, quantity)
```

`demand` é a tabela de fatos (uma linha por peça/rota/dia); `part_numbers`
e `routes` são as dimensões. Schema completo em
[`sql/01_schema.sql`](sql/01_schema.sql).

## Como rodar

```bash
pip install -r requirements.txt
python scripts/generate_synthetic_data.py   # gera os CSVs em data/raw/
python scripts/load_to_db.py                # cria ppcp.db (SQLite) e carrega os dados
sqlite3 ppcp.db < sql/02_queries.sql         # roda as queries
```

## Queries e resultados

Todas as queries completas estão em [`sql/02_queries.sql`](sql/02_queries.sql).
Abaixo, os resultados reais obtidos sobre a base sintética gerada.

### 1. Demanda total por rota (últimos 6 meses)

| rota | demanda_total | dias_com_movimento |
|---|---|---|
| Rota Sul | 21.569 | 180 |
| Rota Oeste | 16.108 | 180 |
| Rota Norte | 13.299 | 180 |
| Rota Leste | 8.764 | 180 |

**Insight:** a Rota Sul concentra ~35% de toda a demanda das quatro rotas —
candidata natural a revisão de capacidade ou redistribuição de peças.

### 2. Peças que mais pesam no total transportado (top 5 de 300)

| code | family | peso_total_kg | % do total | % acumulado |
|---|---|---|---|---|
| PN-1184 | Elétrico | 6.047,6 | 2,16% | 2,16% |
| PN-1109 | Suspensão | 5.148,8 | 1,84% | 3,99% |
| PN-1279 | Suspensão | 5.134,8 | 1,83% | 5,82% |
| PN-1152 | Chassi | 5.018,2 | 1,79% | 7,61% |
| PN-1284 | Interior | 4.801,9 | 1,71% | 9,32% |

**Insight:** usa `SUM() OVER ()` para % do total e `SUM() OVER (ORDER BY ...)`
para % acumulado — a mesma lógica de curva ABC usada em priorização de
estoque/transporte.

### 3. P95 da demanda diária por rota (dimensionamento de capacidade)

| rota | p95_demanda_diaria |
|---|---|
| Rota Leste | 90 |
| Rota Norte | 127 |
| Rota Oeste | 174 |
| Rota Sul | 224 |

**Insight:** dimensionar pela média subestimaria a capacidade necessária;
o P95 é o número que garante atendimento em 95% dos dias sem superdimensionar
para os 5% de picos extremos.

### 4. Dias em que a rota excedeu a capacidade da carretinha

| rota | data | peso transportado (kg) | capacidade (kg) | excedente (kg) |
|---|---|---|---|---|
| Rota Sul | 2026-05-29 | 1.723,4 | 1.200,0 | 523,4 |
| Rota Sul | 2026-01-13 | 1.419,3 | 1.200,0 | 219,3 |
| Rota Oeste | 2026-02-02 | 1.094,1 | 950,0 | 144,1 |
| Rota Norte | 2026-04-02 | 975,6 | 850,0 | 125,6 |

**Insight:** a Rota Sul não excede a capacidade só nos dias de pico — o
excedente do dia 29/05 é maior que qualquer outro, sinal de que vale
investigar se houve um evento pontual (ex.: reposição concentrada) ou se a
capacidade está subdimensionada para a operação normal.

### 5. Rota com maior variabilidade de demanda

| rota | média diária | desvio padrão |
|---|---|---|
| Rota Sul | 119,8 | 60,1 |
| Rota Oeste | 89,5 | 46,5 |
| Rota Norte | 73,9 | 31,8 |
| Rota Leste | 48,7 | 24,6 |

**Insight:** a Rota Sul é, ao mesmo tempo, a de maior volume e maior
variabilidade — a que mais se beneficiaria de um plano de contingência de
capacidade.

## Tecnologias

- **Python** (pandas, numpy) — geração dos dados sintéticos
- **SQLite** — banco de dados (schema, JOIN, GROUP BY, HAVING, CTE, window
  functions)
- **SQL** como linguagem principal de análise

## Estrutura do repositório

```
├── data/raw/                     # CSVs sintéticos gerados pelo script
├── sql/
│   ├── 01_schema.sql              # criação das tabelas
│   └── 02_queries.sql             # as 5 queries de análise
├── scripts/
│   ├── generate_synthetic_data.py # gera os dados sintéticos
│   └── load_to_db.py              # cria o SQLite e carrega os dados
├── requirements.txt
└── README.md
```

## Próximos passos

- Adicionar uma versão em Power BI conectada ao SQLite para visualização dos
  indicadores.
- Simular um cenário de redistribuição de peças entre rotas para equilibrar
  a demanda (a Rota Sul absorveria parte de sua carga para a Rota Leste, que
  hoje tem folga de capacidade).
