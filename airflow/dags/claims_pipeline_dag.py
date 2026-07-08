from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, '/opt/airflow')

default_args = {
    'owner': 'vaishnavi',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
}

def extract_task():
    from ingestion.extract import extract_claims, extract_icd10_codes
    claims_df = extract_claims()
    icd10_df = extract_icd10_codes()
    print(f"Extracted {len(claims_df)} claims and {len(icd10_df)} ICD-10 codes")

def upload_task():
    from ingestion.upload_to_gcs import upload_file_to_gcs, download_icd10
    upload_file_to_gcs(
        local_path='data/claims_raw.csv',
        gcs_path='raw/claims/claims_raw.csv'
    )
    download_icd10()
    upload_file_to_gcs(
        local_path='data/icd10_codes.csv',
        gcs_path='raw/icd10/icd10_codes.csv'
    )

def load_raw_task():
    from google.cloud import bigquery
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/gcp-key.json"
    client = bigquery.Client()
    query = """
        LOAD DATA OVERWRITE `healthcare-claims-cvs.healthcare_raw.claims_raw`
        FROM FILES (
            format = 'CSV',
            uris = ['gs://healthcare-claims-vaishnavi-2026/raw/claims/claims_raw.csv'],
            field_delimiter = '|',
            skip_leading_rows = 1
        )
    """
    client.query(query).result()
    print("Raw claims loaded to BigQuery healthcare_raw dataset")

def quality_check_task():
    from google.cloud import storage
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/gcp-key.json"
    client = storage.Client()
    bucket = client.bucket('healthcare-claims-vaishnavi-2026')
    blob = bucket.blob('raw/claims/claims_raw.csv')
    if not blob.exists():
        raise ValueError("claims_raw.csv not found in GCS — pipeline aborted")
    print("File-level quality check passed — claims_raw.csv exists in GCS")

with DAG(
    dag_id='healthcare_claims_pipeline',
    default_args=default_args,
    description='End-to-end healthcare claims pipeline with dbt medallion architecture',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['healthcare', 'claims', 'cvs', 'dbt']
) as dag:

    t1 = PythonOperator(
        task_id='extract',
        python_callable=extract_task
    )

    t2 = PythonOperator(
        task_id='upload_to_gcs',
        python_callable=upload_task
    )

    t3 = PythonOperator(
        task_id='load_raw_to_bigquery',
        python_callable=load_raw_task
    )

    t4 = PythonOperator(
        task_id='quality_checks',
        python_callable=quality_check_task
    )

    t5 = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/healthcare_dbt && dbt run --profiles-dir /opt/airflow/healthcare_dbt',
        env={
            'GOOGLE_APPLICATION_CREDENTIALS': '/opt/airflow/gcp-key.json'
        }
    )

    t6 = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/healthcare_dbt && dbt test --profiles-dir /opt/airflow/healthcare_dbt',
        env={
            'GOOGLE_APPLICATION_CREDENTIALS': '/opt/airflow/gcp-key.json'
        }
    )

    t1 >> t2 >> t3 >> t4 >> t5 >> t6