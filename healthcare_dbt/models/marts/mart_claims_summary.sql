WITH claims AS (
    SELECT * FROM {{ ref('int_claims_deduplicated') }}
),

icd AS (
    SELECT * FROM {{ ref('stg_icd_codes') }}
),

states AS (
    SELECT * FROM {{ ref('state_codes') }}
),

final AS (
    SELECT
        SUBSTR(c.claim_from_date, 1, 7)     AS claim_month,
        COALESCE(s.state_name, 'Unknown')    AS state,
        c.diagnosis_code,
        i.diagnosis_description,
        i.diagnosis_category,
        COUNT(c.claim_id)                    AS total_claims,
        SUM(c.claim_amount)                  AS total_paid,
        SUM(c.total_charges)                 AS total_charged,
        AVG(c.claim_amount)                  AS avg_paid_per_claim,
        SUM(c.total_charges - c.claim_amount) AS total_denied_amount
    FROM claims c
    LEFT JOIN icd i
        ON c.diagnosis_code = i.diagnosis_code
    LEFT JOIN states s
        ON SAFE_CAST(c.provider_state_code AS INT64) = s.state_code
    GROUP BY 1, 2, 3, 4, 5
)

SELECT * FROM final