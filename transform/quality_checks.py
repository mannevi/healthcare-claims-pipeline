import pandas as pd
import os
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

BUCKET_NAME = "healthcare-claims-vaishnavi-2026"

def save_failed_records(df, check_name):
    """Save failed records to GCS quarantine folder"""
    if len(df) > 0:
        local_path = f"data/failed_{check_name}.csv"
        df.to_csv(local_path, index=False)
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"quarantine/failed_{check_name}.csv")
        blob.upload_from_filename(local_path)
        print(f"  Saved {len(df)} failed records to quarantine/{check_name}.csv")

def run_quality_checks(fact_claims, dim_patient, dim_provider, dim_diagnosis):
    print("\nRunning data quality checks...")
    print("-" * 40)

    total_checks = 0
    passed_checks = 0

    # Check 1: No null claim_id
    total_checks += 1
    failed = fact_claims[fact_claims['claim_id'].isnull()]
    if len(failed) == 0:
        print("✓ Check 1 PASSED: No null claim_ids")
        passed_checks += 1
    else:
        print(f"✗ Check 1 FAILED: {len(failed)} null claim_ids found")
        save_failed_records(failed, "null_claim_id")

    # Check 2: No null patient_id
    total_checks += 1
    failed = fact_claims[fact_claims['patient_id'].isnull()]
    if len(failed) == 0:
        print("✓ Check 2 PASSED: No null patient_ids")
        passed_checks += 1
    else:
        print(f"✗ Check 2 FAILED: {len(failed)} null patient_ids found")
        save_failed_records(failed, "null_patient_id")

    # Check 3: No duplicate claim_ids
    total_checks += 1
    failed = fact_claims[fact_claims.duplicated(subset=['claim_id'])]
    if len(failed) == 0:
        print("✓ Check 3 PASSED: No duplicate claim_ids")
        passed_checks += 1
    else:
        print(f"✗ Check 3 FAILED: {len(failed)} duplicate claim_ids found")
        save_failed_records(failed, "duplicate_claim_id")

    # Check 4: claim_amount >= 0
    total_checks += 1
    failed = fact_claims[fact_claims['claim_amount'] < 0]
    if len(failed) == 0:
        print("✓ Check 4 PASSED: No negative claim amounts")
        passed_checks += 1
    else:
        print(f"✗ Check 4 FAILED: {len(failed)} negative claim amounts found")
        save_failed_records(failed, "negative_claim_amount")

    # Check 5: No null diagnosis_code
    total_checks += 1
    failed = fact_claims[fact_claims['diagnosis_code'].isnull()]
    if len(failed) == 0:
        print("✓ Check 5 PASSED: No null diagnosis codes")
        passed_checks += 1
    else:
        print(f"✗ Check 5 FAILED: {len(failed)} null diagnosis codes found")
        save_failed_records(failed, "null_diagnosis_code")

    # Check 6: No empty claim dates
    total_checks += 1
    failed = fact_claims[
        (fact_claims['claim_from_date'].isnull()) |
        (fact_claims['claim_from_date'] == 'nan') |
        (fact_claims['claim_from_date'] == '')
    ]
    if len(failed) == 0:
        print("✓ Check 6 PASSED: No empty claim dates")
        passed_checks += 1
    else:
        print(f"✗ Check 6 FAILED: {len(failed)} empty claim dates found")
        save_failed_records(failed, "empty_claim_date")

    # Summary
    print("-" * 40)
    print(f"Quality Report: {passed_checks}/{total_checks} checks passed")
    print(f"Records checked: {len(fact_claims)}")
    print(f"Pass rate: {round(passed_checks/total_checks*100)}%")

    return passed_checks == total_checks

if __name__ == "__main__":
    
    from ingestion.extract import extract_claims, extract_icd10_codes
    from transform.transform import transform_claims

    claims_df = extract_claims()
    icd10_df  = extract_icd10_codes()

    fact_claims, dim_patient, dim_provider, dim_diagnosis = transform_claims(
        claims_df, icd10_df
    )

    all_passed = run_quality_checks(
        fact_claims, dim_patient, dim_provider, dim_diagnosis
    )

    if all_passed:
        print("\nAll checks passed. Safe to load.")
    else:
        print("\nSome checks failed. Review quarantine folder.")