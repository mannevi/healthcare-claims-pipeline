import os
import pandas as pd
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

BUCKET_NAME = "healthcare-claims-vaishnavi-2026"

def upload_file_to_gcs(local_path, gcs_path):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path)
    print(f"Uploaded {local_path} to gs://{BUCKET_NAME}/{gcs_path}")

def download_icd10():
    url = "https://raw.githubusercontent.com/k4m1113/ICD-10-CSV/master/codes.csv"
    df = pd.read_csv(url, header=None, names=['code', 'description'])
    df.to_csv('data/icd10_codes.csv', index=False)
    print(f"Downloaded {len(df)} ICD-10 codes to data/icd10_codes.csv")

if __name__ == "__main__":
    # Upload claims
    upload_file_to_gcs(
        local_path="data/claims_raw.csv",
        gcs_path="raw/claims/claims_raw.csv"
    )

    # Download ICD-10 then upload
    download_icd10()
    upload_file_to_gcs(
        local_path="data/icd10_codes.csv",
        gcs_path="raw/icd10/icd10_codes.csv"
    )

    print("All uploads complete.")