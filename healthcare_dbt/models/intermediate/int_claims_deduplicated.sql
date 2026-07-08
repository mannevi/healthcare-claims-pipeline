WITH ranked_claims AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY claim_id
            ORDER BY claim_from_date DESC
        ) AS row_num
    FROM {{ ref('stg_claims') }}
),

deduplicated AS (
    SELECT * EXCEPT(row_num)
    FROM ranked_claims
    WHERE row_num = 1
)

SELECT * FROM deduplicated