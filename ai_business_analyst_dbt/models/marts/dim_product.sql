SELECT
    product_id,
    product_category_name_english
FROM {{ ref('stg_products') }}