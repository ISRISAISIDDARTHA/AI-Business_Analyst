SELECT
    oi.order_id,
    oi.order_item_id,
    o.order_status,
    oi.product_id,
    oi.seller_id,
    c.customer_unique_id,
    TO_CHAR(o.order_purchase_ts, 'YYYYMMDD')::int AS date_key,
    oi.price,
    oi.freight_value
FROM {{ ref('stg_order_items') }} oi
JOIN {{ ref('stg_orders') }} o
    ON oi.order_id = o.order_id
JOIN {{ source('raw', 'raw_customers') }} c
    ON o.customer_id = c.customer_id