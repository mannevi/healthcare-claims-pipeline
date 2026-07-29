import pandas as pd
import os

def extract_claims():
    print("Extracting claims data...")
    df = pd.read_csv('data/claims_raw.csv', sep='|', low_memory=False)
    print(f"Claims extracted: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def extract_icd10_codes():
    print("Extracting ICD-10 codes from URL...")
    url = "https://raw.githubusercontent.com/k4m1113/ICD-10-CSV/master/codes.csv"
    # The source file has 6 unnamed columns:
    # 1. category-level code, 2. sub-code, 3. full ICD-10 code,
    # 4. short description, 5. long description, 6. category
    # Previous version only captured columns 4 and 6, silently dropping
    # the actual code column (3) - which is why diagnosis_code in the
    # marts never matched real claim diagnosis codes.
    df = pd.read_csv(
        url,
        header=None,
        names=['category_code', 'sub_code', 'icd10_code', 'short_description',
               'long_description', 'category'],
    )
    # Keep only what stg_icd_codes.sql actually needs
    df = df[['icd10_code', 'short_description', 'category']].rename(
        columns={'icd10_code': 'code', 'short_description': 'description'}
    )
    print(f"ICD-10 codes extracted: {df.shape[0]} rows")
    return df

if __name__ == "__main__":
    claims_df = extract_claims()
    icd10_df = extract_icd10_codes()
    print("Extraction complete.")