SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    CAST(NULLIF(shipping_limit_date, '') AS TIMESTAMP) AS shipping_limit_ts,
    price,
    freight_value
FROM {{ source('raw', 'raw_order_items') }}