# Star Schema Design — AI Business Analyst

## Grain
`fact_order_line_items`: one row per order line item (matches raw `order_items` grain).
Chosen over order-level grain because root-cause analysis needs to slice revenue
by product/category/seller, which order-level grain cannot support (an order can
span multiple products/categories).

## Fact Table: fact_order_line_items

| Column | Type | Description |
|---|---|---|
| order_id | varchar | degenerate dimension, needed for order-level rollups (e.g. items per order) |
| order_status | varchar | degenerate dimension, no separate table — no independent attributes/hierarchy to justify one |
| product_id | varchar (FK) | → dim_product |
| seller_id | varchar (FK) | → dim_seller |
| customer_unique_id | varchar (FK) | → dim_customer |
| date_key | int (FK) | → dim_date, derived from order_purchase_timestamp |
| price | numeric | measure |
| freight_value | numeric | measure |

**Revenue rule:** `canceled` and `unavailable` order_status excluded from revenue
sums, regardless of whether priced line items exist for that order (461 canceled
orders were found with priced items — still excluded, since "canceled" means the
sale didn't happen). Applied at query/model time via a filtered mart, not baked
into the raw fact table, so cancellation-rate analysis is still possible.

## Dimensions

### dim_product
| Column | Description |
|---|---|
| product_id (key) | natural key |
| product_category_name_english | joined from product_category_name_translation.csv; raw category names are in Portuguese |

Excluded: weight/dimensions, photo count, name/description length — no clear
analytical use case for this project's root-cause questions.

### dim_customer
| Column | Description |
|---|---|
| customer_unique_id (key) | NOT customer_id — customer_id is generated per order (99,441 rows), customer_unique_id identifies the actual person (96,096 rows). Using customer_id would make every repeat customer look like a distinct one-time customer and break repeat-purchase/LTV analysis. |
| customer_city | |
| customer_state | |
| customer_zip_code_prefix | |

**Bridge/join note:** raw `orders` only has `customer_id`. To populate the fact
table's `customer_unique_id` FK, join `orders.customer_id` → raw `customers.customer_id`
→ `customers.customer_unique_id`.

### dim_seller
| Column | Description |
|---|---|
| seller_id (key) | natural key, no dual-ID issue like customers |
| seller_city | |
| seller_state | |
| seller_zip_code_prefix | |

### dim_date
| Column | Description |
|---|---|
| date_key (key) | YYYYMMDD integer |
| full_date | actual date type |
| year | |
| month | |
| month_name | |
| quarter | |
| day_of_week | |
| day_name | |
| is_weekend | boolean |

Generated as a standalone calendar table (dbt seed or generation script),
not derived from raw data — covers Olist's order date range (~2016–2018).
Built as a real dimension (not raw timestamps on the fact table) because
the project's core purpose is explaining metric change *over time*, which
needs month/quarter/day-of-week rollups available without recomputing them
in every query.

## Rejected: dim_geography
Considered as a separate dimension (raw `geolocation` table exists), but
rejected — city/state/zip already live directly on dim_customer and dim_seller,
and geolocation's only additional value (lat/long) isn't needed for root-cause
analysis, which needs "which region," not coordinates. Adding it would be an
extra join with no analytical benefit for this project.

## Diagram

              dim_product
                   |
  dim_customer --- fact_order_line_items --- dim_seller
                   |
                dim_date