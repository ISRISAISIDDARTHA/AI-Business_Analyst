SELECT
    seller_id,
    seller_city,
    seller_state,
    seller_zip_code_prefix
FROM {{ source('raw', 'raw_sellers') }}