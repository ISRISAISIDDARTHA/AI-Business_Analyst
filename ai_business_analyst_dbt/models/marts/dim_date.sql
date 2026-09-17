WITH date_spine AS (
    SELECT generate_series(
        '2016-01-01'::date,
        '2018-12-31'::date,
        '1 day'::interval
    )::date AS full_date
)

SELECT
    TO_CHAR(full_date, 'YYYYMMDD')::int AS date_key,
    full_date,
    EXTRACT(YEAR FROM full_date)::int AS year,
    EXTRACT(MONTH FROM full_date)::int AS month,
    TO_CHAR(full_date, 'Month') AS month_name,
    EXTRACT(QUARTER FROM full_date)::int AS quarter,
    EXTRACT(ISODOW FROM full_date)::int AS day_of_week,
    TO_CHAR(full_date, 'Day') AS day_name,
    (EXTRACT(ISODOW FROM full_date) IN (6, 7)) AS is_weekend
FROM date_spine