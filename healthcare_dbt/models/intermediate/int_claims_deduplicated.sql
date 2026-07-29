WITH ranked_claims AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY claim_id
            -- claim_from_date alone isn't unique when a claim has multiple
            -- service lines on the same date - claim_line_num as a
            -- tiebreaker makes which "representative" row gets kept a
            -- deliberate choice (always line 1) instead of arbitrary.
            ORDER BY claim_from_date DESC, claim_line_num ASC
        ) AS row_num
    FROM {{ ref('stg_claims') }}
),

deduplicated AS (
    SELECT * EXCEPT(row_num)
    FROM ranked_claims
    WHERE row_num = 1
)

SELECT * FROM deduplicated