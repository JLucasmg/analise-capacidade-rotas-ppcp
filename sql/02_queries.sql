-- ============================================================
-- Q1. Demanda total por rota nos últimos 6 meses
-- Responde: qual rota tem maior volume de movimentação?
-- ============================================================
SELECT
    r.name                     AS rota,
    SUM(d.quantity)            AS demanda_total,
    COUNT(DISTINCT d.demand_date) AS dias_com_movimento
FROM demand d
JOIN routes r ON r.id = d.route_id
WHERE d.demand_date >= date((SELECT MAX(demand_date) FROM demand), '-6 months')
GROUP BY r.name
ORDER BY demanda_total DESC;


-- ============================================================
-- Q2. Peças que mais contribuem para o peso total transportado
-- Responde: quais Part Numbers concentram o maior risco de peso
-- transportado (lógica 80/20)?
-- Usa CTE + window function.
-- ============================================================
WITH peso_por_peca AS (
    SELECT
        p.code,
        p.family,
        SUM(p.weight_kg * d.quantity) AS peso_total_kg
    FROM demand d
    JOIN part_numbers p ON p.id = d.part_number_id
    GROUP BY p.code, p.family
)
SELECT
    code,
    family,
    ROUND(peso_total_kg, 1) AS peso_total_kg,
    ROUND(100.0 * peso_total_kg / SUM(peso_total_kg) OVER (), 2) AS pct_do_total,
    ROUND(100.0 * SUM(peso_total_kg) OVER (ORDER BY peso_total_kg DESC)
          / SUM(peso_total_kg) OVER (), 2) AS pct_acumulado
FROM peso_por_peca
ORDER BY peso_total_kg DESC
LIMIT 10;


-- ============================================================
-- Q3. Percentil 95 (P95) da demanda diária por rota
-- Responde: qual capacidade a rota precisa suportar para atender
-- 95% dos dias sem estourar? (dimensionamento de capacidade)
-- ============================================================
WITH demanda_diaria AS (
    SELECT route_id, demand_date, SUM(quantity) AS qty_dia
    FROM demand
    GROUP BY route_id, demand_date
),
ranked AS (
    SELECT
        route_id,
        qty_dia,
        PERCENT_RANK() OVER (PARTITION BY route_id ORDER BY qty_dia) AS pr
    FROM demanda_diaria
)
SELECT
    r.name AS rota,
    MIN(qty_dia) AS p95_demanda_diaria
FROM ranked
JOIN routes r ON r.id = ranked.route_id
WHERE pr >= 0.95
GROUP BY r.name;


-- ============================================================
-- Q4. Dias em que a rota ultrapassou a capacidade da carretinha
-- Responde: em quantos dias e por quanto a rota excedeu o limite?
-- Usa JOIN + GROUP BY + HAVING.
-- ============================================================
SELECT
    r.name AS rota,
    d.demand_date,
    ROUND(SUM(p.weight_kg * d.quantity), 1) AS peso_transportado_kg,
    r.trailer_capacity_kg,
    ROUND(SUM(p.weight_kg * d.quantity) - r.trailer_capacity_kg, 1) AS excedente_kg
FROM demand d
JOIN routes r ON r.id = d.route_id
JOIN part_numbers p ON p.id = d.part_number_id
GROUP BY r.name, d.demand_date, r.trailer_capacity_kg
HAVING peso_transportado_kg > r.trailer_capacity_kg
ORDER BY excedente_kg DESC
LIMIT 10;


-- ============================================================
-- Q5. Rota com maior variabilidade de demanda (desvio padrão)
-- Responde: qual rota é mais imprevisível e merece atenção no
-- planejamento de capacidade?
-- ============================================================
WITH demanda_diaria AS (
    SELECT route_id, demand_date, SUM(quantity) AS qty_dia
    FROM demand
    GROUP BY route_id, demand_date
)
SELECT
    r.name AS rota,
    ROUND(AVG(qty_dia), 1) AS media_diaria,
    ROUND(
        SQRT(AVG(qty_dia * qty_dia) - AVG(qty_dia) * AVG(qty_dia)), 1
    ) AS desvio_padrao
FROM demanda_diaria dd
JOIN routes r ON r.id = dd.route_id
GROUP BY r.name
ORDER BY desvio_padrao DESC;
