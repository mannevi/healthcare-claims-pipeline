from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, '/opt/airflow')

from ingestion.extract import extract_claims, extract_icd10_codes
from ingestion.upload_to_gcs import upload_file_to_gcs
from transform.transform import transform_claims
from transform.quality_checks import run_quality_checks
from transform.load import load_all

default_args = {
    'owner': 'vaishnavi',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
}

def extract_task():
    claims_df = extract_claims()
    icd10_df = extract_icd10_codes()
    return "extraction complete"

def upload_task():
    upload_file_to_gcs(
        local_path='data/claims_raw.csv',
        gcs_path='raw/claims/claims_raw.csv'
    )

def transform_task():
    from ingestion.extract import extract_claims, extract_icd10_codes
    from transform.transform import transform_claims
    claims_df = extract_claims()
    icd10_df = extract_icd10_codes()
    fact_claims, dim_patient, dim_provider, dim_diagnosis = transform_claims(
        claims_df, icd10_df
    )
    return "transform complete"

def quality_task():
    from ingestion.extract import extract_claims, extract_icd10_codes
    from transform.transform import transform_claims
    from transform.quality_checks import run_quality_checks
    claims_df = extract_claims()
    icd10_df = extract_icd10_codes()
    fact_claims, dim_patient, dim_provider, dim_diagnosis = transform_claims(
        claims_df, icd10_df
    )
    all_passed = run_quality_checks(
        fact_claims, dim_patient, dim_provider, dim_diagnosis
    )
    if not all_passed:
        raise ValueError("Quality checks failed. Load aborted.")

def load_task():
    from ingestion.extract import extract_claims, extract_icd10_codes
    from transform.transform import transform_claims
    from transform.load import load_all
    claims_df = extract_claims()
    icd10_df = extract_icd10_codes()
    fact_claims, dim_patient, dim_provider, dim_diagnosis = transform_claims(
        claims_df, icd10_df
    )
    load_all(fact_claims, dim_patient, dim_provider, dim_diagnosis)

with DAG(
    dag_id='healthcare_claims_pipeline',
    default_args=default_args,
    description='End-to-end healthcare claims pipeline',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['healthcare', 'claims', 'cvs']
) as dag:

    t1 = PythonOperator(task_id='extract', python_callable=extract_task)
    t2 = PythonOperator(task_id='upload_to_gcs', python_callable=upload_task)
    t3 = PythonOperator(task_id='transform', python_callable=transform_task)
    t4 = PythonOperator(task_id='quality_checks', python_callable=quality_task)
    t5 = PythonOperator(task_id='load_to_bigquery', python_callable=load_task)

    t1 >> t2 >> t3 >> t4 >> t5