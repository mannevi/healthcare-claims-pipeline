WITH claims AS (
    SELECT * FROM {{ ref('int_claims_deduplicated') }}
),

icd AS (
    SELECT * FROM {{ ref('stg_icd_codes') }}
),

final AS (
    SELECT
        c.diagnosis_code,
        i.diagnosis_description,
        i.diagnosis_category,
        COUNT(c.claim_id)           AS claim_count,
        SUM(c.claim_amount)         AS total_cost,
        AVG(c.claim_amount)         AS avg_cost_per_claim,
        MAX(c.claim_amount)         AS max_claim,
        MIN(c.claim_amount)         AS min_claim,
        STDDEV(c.claim_amount)      AS cost_stddev
    FROM claims c
    LEFT JOIN icd i
        ON c.diagnosis_code = i.diagnosis_code
    GROUP BY 1, 2, 3
)

SELECT * FROM final
ORDER BY total_cost DESC