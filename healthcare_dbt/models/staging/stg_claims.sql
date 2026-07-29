WITH source AS (
    SELECT * FROM {{ source('healthcare_raw', 'claims_raw') }}
),

renamed AS (
    SELECT
        -- IDs
        CAST(CLM_ID AS STRING)      AS claim_id,
        CAST(BENE_ID AS STRING)     AS patient_id,
        CAST(PRVDR_NUM AS STRING)   AS provider_id,
        CAST(CLM_LINE_NUM AS INT64) AS claim_line_num,

        -- Diagnosis
        CAST(PRNCPAL_DGNS_CD AS STRING)     AS diagnosis_code,
        CAST(CLM_DRG_CD AS STRING)          AS drg_code,

        -- Amounts
        CAST(CLM_PMT_AMT AS FLOAT64)        AS claim_amount,
        CAST(CLM_TOT_CHRG_AMT AS FLOAT64)   AS total_charges,

        -- Dates
        CAST(CLM_FROM_DT AS STRING)         AS claim_from_date,
        CAST(CLM_THRU_DT AS STRING)         AS claim_thru_date,

        -- Provider location
        CAST(PRVDR_STATE_CD AS STRING)      AS provider_state_code,
        CAST(ORG_NPI_NUM AS STRING)         AS npi_number,

        -- Patient info
        CAST(PTNT_DSCHRG_STUS_CD AS STRING) AS discharge_status,
        CAST(CLM_IP_ADMSN_TYPE_CD AS STRING) AS admission_type

    FROM source
    WHERE CLM_ID IS NOT NULL
      AND BENE_ID IS NOT NULL
      AND PRVDR_NUM IS NOT NULL
      AND CLM_PMT_AMT >= 0
)

SELECT * FROM renamed