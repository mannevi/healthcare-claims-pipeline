import os
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

BUCKET_NAME = "healthcare-claims-vaishnavi-2026"

def upload_file_to_gcs(local_path, gcs_path):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path)
    print(f"Uploaded {local_path} to gs://{BUCKET_NAME}/{gcs_path}")

if __name__ == "__main__":
    upload_file_to_gcs(
        local_path="data/claims_raw.csv",
        gcs_path="raw/claims/claims_raw.csv"
    )
    print("Upload complete.")