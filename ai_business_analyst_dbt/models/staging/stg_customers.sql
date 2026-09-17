SELECT DISTINCT ON (customer_unique_id)
    customer_unique_id,
    customer_city,
    customer_state,
    customer_zip_code_prefix
FROM {{ source('raw', 'raw_customers') }}
ORDER BY customer_unique_id