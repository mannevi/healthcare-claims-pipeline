WITH source AS (
    SELECT * FROM {{ source('healthcare_raw', 'icd_codes_raw') }}
),

renamed AS (
    SELECT
        TRIM(UPPER(code))          AS diagnosis_code,
        TRIM(description)          AS diagnosis_description,
        TRIM(category)             AS diagnosis_category
    FROM source
    WHERE code IS NOT NULL
)

SELECT * FROM renamed