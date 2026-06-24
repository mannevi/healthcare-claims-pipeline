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
    df = pd.read_csv(url, header=None, names=['code', 'description'])
    print(f"ICD-10 codes extracted: {df.shape[0]} rows")
    return df

if __name__ == "__main__":
    claims_df = extract_claims()
    icd10_df = extract_icd10_codes()
    print("Extraction complete.")