import pandas as pd
from app.config.db import get_engine

RAW_DATA_DIR = "data/raw"

FILES_TO_TABLES = {
    "olist_orders_dataset.csv": "raw_orders",
    "olist_customers_dataset.csv": "raw_customers",
    "olist_order_items_dataset.csv": "raw_order_items",
    "olist_order_payments_dataset.csv": "raw_order_payments",
    "olist_order_reviews_dataset.csv": "raw_order_reviews",
    "olist_products_dataset.csv": "raw_products",
    "olist_sellers_dataset.csv": "raw_sellers",
    "olist_geolocation_dataset.csv": "raw_geolocation",
    "product_category_name_translation.csv": "raw_category_translation",
}

def load_all():
    engine = get_engine()
    for filename, table_name in FILES_TO_TABLES.items():
        path = f"{RAW_DATA_DIR}/{filename}"
        print(f"Loading {filename} -> {table_name}")
        df = pd.read_csv(path)
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"{len(df)} rows loaded")

if __name__ == "__main__":
    load_all()