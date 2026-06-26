import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

PROJECT_ID = "healthcare-claims-cvs"
DATASET_ID = "healthcare_claims"

def load_table(df, table_name):
    client = bigquery.Client()
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"Loaded {len(df)} rows into {table_id}")

def load_all(fact_claims, dim_patient, dim_provider, dim_diagnosis):
    print("Loading dimension tables first...")
    load_table(dim_patient,   "dim_patient")
    load_table(dim_provider,  "dim_provider")
    load_table(dim_diagnosis, "dim_diagnosis")
    
    print("Loading fact table...")
    load_table(fact_claims,   "fact_claims")
    
    print("All tables loaded successfully.")

if __name__ == "__main__":
    from ingestion.extract import extract_claims, extract_icd10_codes
    from transform.transform import transform_claims

    claims_df = extract_claims()
    icd10_df  = extract_icd10_codes()

    fact_claims, dim_patient, dim_provider, dim_diagnosis = transform_claims(claims_df, icd10_df)

    load_all(fact_claims, dim_patient, dim_provider, dim_diagnosis)