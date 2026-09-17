SELECT
    p.product_id,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS product_category_name_english
FROM {{ source('raw', 'raw_products') }} p
LEFT JOIN {{ source('raw', 'raw_category_translation') }} t
    ON p.product_category_name = t.product_category_name