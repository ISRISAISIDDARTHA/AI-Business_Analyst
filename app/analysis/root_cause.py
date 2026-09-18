import pandas as pd
from app.config.db import get_engine

# Each entry describes how to join and group by one dimension.
# This is the "parameters" we talked about — table, group-by column, join key.
DIMENSIONS = {
    "category": {
        "table": "analytics.dim_product",
        "alias": "dp",
        "group_col": "product_category_name_english",
        "fact_join_col": "product_id",
    },
    "region": {
        "table": "analytics.dim_customer",
        "alias": "dc",
        "group_col": "customer_state",
        "fact_join_col": "customer_unique_id",
    },
    "seller": {
        "table": "analytics.dim_seller",
        "alias": "ds",
        "group_col": "seller_state",
        "fact_join_col": "seller_id",
    },
}

def analyze_dimension(engine, dim_key: str, year: int, month_a: int, month_b: int) -> pd.DataFrame:
    """
    Runs the conditional-aggregation query for ONE dimension (category/region/seller),
    comparing month_a vs month_b revenue, and returns contribution % per group.
    """
    dim = DIMENSIONS[dim_key]

    query = f"""
    WITH group_revenue AS (
        SELECT
            {dim['alias']}.{dim['group_col']} AS group_value,
            SUM(CASE WHEN dd.month = {month_a} THEN f.price ELSE 0 END) AS period_a_revenue,
            SUM(CASE WHEN dd.month = {month_b} THEN f.price ELSE 0 END) AS period_b_revenue
        FROM analytics.fct_order_line_items f
        JOIN analytics.dim_date dd ON f.date_key = dd.date_key
        JOIN {dim['table']} {dim['alias']} ON f.{dim['fact_join_col']} = {dim['alias']}.{dim['fact_join_col']}
        WHERE f.order_status NOT IN ('canceled', 'unavailable')
          AND dd.year = {year}
          AND dd.month IN ({month_a}, {month_b})
        GROUP BY {dim['alias']}.{dim['group_col']}
    ),
    totals AS (
        SELECT SUM(period_a_revenue) AS total_a, SUM(period_b_revenue) AS total_b
        FROM group_revenue
    )
    SELECT
        '{dim_key}' AS dimension,
        gr.group_value,
        ROUND(gr.period_a_revenue::numeric, 2) AS period_a_revenue,
        ROUND(gr.period_b_revenue::numeric, 2) AS period_b_revenue,
        ROUND((gr.period_b_revenue - gr.period_a_revenue)::numeric, 2) AS change,
        ROUND(
            ((gr.period_b_revenue - gr.period_a_revenue) / NULLIF(t.total_b - t.total_a, 0) * 100)::numeric,
            1
        ) AS contribution_pct
    FROM group_revenue gr, totals t
    ORDER BY ABS(gr.period_b_revenue - gr.period_a_revenue) DESC
    """

    return pd.read_sql(query, engine)


def find_root_cause(year: int, month_a: int, month_b: int, top_n: int = 3) -> dict:
    """
    Runs the analysis across ALL dimensions, finds the single biggest driver
    across all of them (not just within one dimension), and returns a
    structured finding — this is what eventually gets handed to the LLM.
    """
    engine = get_engine()
    all_results = []

    for dim_key in DIMENSIONS:
        df = analyze_dimension(engine, dim_key, year, month_a, month_b)
        all_results.append(df)

    combined = pd.concat(all_results, ignore_index=True)

    # The single row with the largest absolute dollar change, across ALL dimensions
    top_driver = combined.reindex(combined["change"].abs().sort_values(ascending=False).index).iloc[0]

    return {
        "period": f"{month_a}/{year} vs {month_b}/{year}",
        "primary_driver": {
            "dimension": top_driver["dimension"],
            "value": top_driver["group_value"],
            "change": float(top_driver["change"]),
            "contribution_pct": float(top_driver["contribution_pct"]),
        },
        "top_movers_by_dimension": {
            dim_key: df.head(top_n).to_dict(orient="records")
            for dim_key, df in zip(DIMENSIONS.keys(), all_results)
        },
    }