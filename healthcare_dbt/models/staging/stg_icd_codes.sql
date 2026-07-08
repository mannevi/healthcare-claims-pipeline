WITH source AS (
    SELECT * FROM {{ source('healthcare_raw', 'icd_codes_raw') }}
),

renamed AS (
    SELECT
        TRIM(UPPER(description))  AS diagnosis_code,
        TRIM(description)         AS diagnosis_description,
        TRIM(category)            AS diagnosis_category
    FROM source
    WHERE description IS NOT NULL
)

SELECT * FROM renamed