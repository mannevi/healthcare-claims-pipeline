import pandas as pd
import os

def transform_claims(claims_df, icd10_df):
    print("Starting transformation...")

    # Step 1: Select only columns we need
    cols = [
        'CLM_ID', 'BENE_ID', 'PRVDR_NUM', 'PRNCPAL_DGNS_CD',
        'CLM_PMT_AMT', 'CLM_TOT_CHRG_AMT', 'CLM_FROM_DT',
        'CLM_THRU_DT', 'CLM_DRG_CD', 'PRVDR_STATE_CD',
        'ORG_NPI_NUM', 'PTNT_DSCHRG_STUS_CD', 'CLM_IP_ADMSN_TYPE_CD'
    ]
    df = claims_df[cols].copy()
    print(f"Step 1 - Selected {len(cols)} columns from {claims_df.shape[1]}")

    # Step 2: Rename columns to meaningful names
    df.rename(columns={
        'CLM_ID':               'claim_id',
        'BENE_ID':              'patient_id',
        'PRVDR_NUM':            'provider_id',
        'PRNCPAL_DGNS_CD':      'diagnosis_code',
        'CLM_PMT_AMT':          'claim_amount',
        'CLM_TOT_CHRG_AMT':     'total_charges',
        'CLM_FROM_DT':          'claim_from_date',
        'CLM_THRU_DT':          'claim_thru_date',
        'CLM_DRG_CD':           'drg_code',
        'PRVDR_STATE_CD':       'provider_state',
        'ORG_NPI_NUM':          'npi_number',
        'PTNT_DSCHRG_STUS_CD':  'discharge_status',
        'CLM_IP_ADMSN_TYPE_CD': 'admission_type'
    }, inplace=True)
    print("Step 2 - Renamed columns to business-friendly names")
# Step 2b: Map numeric state codes to state names
    state_map = {
        1: 'Alabama', 2: 'Alaska', 3: 'Arizona', 4: 'Arkansas',
        5: 'California', 6: 'Colorado', 7: 'Connecticut', 8: 'Delaware',
        9: 'District of Columbia', 10: 'Florida', 11: 'Georgia',
        12: 'Hawaii', 13: 'Idaho', 14: 'Illinois', 15: 'Indiana',
        16: 'Iowa', 17: 'Kansas', 18: 'Kentucky', 19: 'Louisiana',
        20: 'Maine', 21: 'Maryland', 22: 'Massachusetts', 23: 'Michigan',
        24: 'Minnesota', 25: 'Mississippi', 26: 'Missouri', 27: 'Montana',
        28: 'Nebraska', 29: 'Nevada', 30: 'New Hampshire', 31: 'New Jersey',
        32: 'New Mexico', 33: 'New York', 34: 'North Carolina',
        35: 'North Dakota', 36: 'Ohio', 37: 'Oklahoma', 38: 'Oregon',
        39: 'Pennsylvania', 40: 'Puerto Rico', 41: 'Rhode Island',
        42: 'South Carolina', 43: 'South Dakota', 44: 'Tennessee',
        45: 'Texas', 46: 'Utah', 47: 'Vermont', 48: 'Virginia',
        49: 'Washington', 50: 'West Virginia', 51: 'Wisconsin',
        52: 'Wyoming', 53: 'Virgin Islands'
    }
    df['provider_state'] = pd.to_numeric(
        df['provider_state'], errors='coerce'
    ).map(state_map).fillna('Unknown')
    print("Step 2b - Mapped state codes to state names")

# Step 3: Fix null values
    df['claim_amount'] = df['claim_amount'].fillna(0)
    df['total_charges'] = df['total_charges'].fillna(0)
    df['diagnosis_code'] = df['diagnosis_code'].fillna('UNKNOWN')
    df['drg_code'] = df['drg_code'].fillna(0)
    df = df.dropna(subset=['claim_id', 'patient_id', 'provider_id'])
    print(f"Step 3 - Handled nulls. Rows remaining: {len(df)}")

    # Step 4: Fix data types
    df['claim_amount'] = pd.to_numeric(df['claim_amount'], errors='coerce').fillna(0)
    df['total_charges'] = pd.to_numeric(df['total_charges'], errors='coerce').fillna(0)
    df['claim_from_date'] = df['claim_from_date'].astype(str)
    df['claim_thru_date'] = df['claim_thru_date'].astype(str)
    df['drg_code'] = df['drg_code'].astype(str)
    print("Step 4 - Fixed data types")
    # Step 5: Remove duplicates
    before = len(df)
    df.drop_duplicates(subset=['claim_id'], inplace=True)
    print(f"Step 5 - Removed {before - len(df)} duplicate claims")

    # Step 6: Join ICD-10 descriptions
    icd10_df.columns = ['diagnosis_code', 'description']
    icd10_df['diagnosis_code'] = icd10_df['diagnosis_code'].str.strip()
    df['diagnosis_code'] = df['diagnosis_code'].str.strip()
    df = df.merge(icd10_df, on='diagnosis_code', how='left')
    df['description'] = df['description'].fillna('Unknown diagnosis')
    print(f"Step 6 - Joined ICD-10 descriptions. Final rows: {len(df)}")

    # Split into 4 tables
    fact_claims = df[[
        'claim_id', 'patient_id', 'provider_id', 'diagnosis_code',
        'claim_amount', 'total_charges', 'claim_from_date',
        'claim_thru_date', 'drg_code'
    ]].copy()

    dim_patient = df[[
        'patient_id', 'provider_state', 'discharge_status', 'admission_type'
    ]].drop_duplicates(subset=['patient_id']).copy()
    dim_patient.rename(columns={'provider_state': 'state'}, inplace=True)

    dim_provider = df[[
        'provider_id', 'provider_state', 'npi_number'
    ]].drop_duplicates(subset=['provider_id']).copy()

    dim_diagnosis = df[[
        'diagnosis_code', 'description'
    ]].drop_duplicates(subset=['diagnosis_code']).copy()

    print("\nTransformation complete.")
    print(f"fact_claims:   {len(fact_claims)} rows")
    print(f"dim_patient:   {len(dim_patient)} rows")
    print(f"dim_provider:  {len(dim_provider)} rows")
    print(f"dim_diagnosis: {len(dim_diagnosis)} rows")

    return fact_claims, dim_patient, dim_provider, dim_diagnosis


if __name__ == "__main__":
    from ingestion.extract import extract_claims, extract_icd10_codes

    claims_df = extract_claims()
    icd10_df  = extract_icd10_codes()

    fact_claims, dim_patient, dim_provider, dim_diagnosis = transform_claims(claims_df, icd10_df)