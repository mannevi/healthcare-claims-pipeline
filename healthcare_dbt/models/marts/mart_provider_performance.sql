WITH claims AS (
    SELECT * FROM {{ ref('int_claims_deduplicated') }}
),

final AS (
    SELECT
        provider_id,
        npi_number,
        provider_state_code                     AS provider_state,
        COUNT(claim_id)                         AS total_claims,
        SUM(claim_amount)                       AS total_paid,
        SUM(total_charges)                      AS total_charged,
        ROUND(
            SUM(claim_amount) /
            NULLIF(SUM(total_charges), 0) * 100, 2
        )                                       AS payment_ratio_pct,
        AVG(claim_amount)                       AS avg_claim_paid,
        MAX(claim_amount)                       AS max_claim,
        MIN(claim_amount)                       AS min_claim
    FROM claims
    GROUP BY 1, 2, 3
)

SELECT * FROM final