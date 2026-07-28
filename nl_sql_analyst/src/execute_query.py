"""
Phase 4: Execution

Takes guardrail-approved SQL and actually runs it against BigQuery,
using the read-only (BigQuery Data Viewer) service account credentials.

This is the step where Layer 4 of our guardrails - read-only credentials -
finally comes into play for real. Even if every check in guardrails.py
somehow failed, these credentials physically cannot write or delete data.
"""

import os
import re
import json
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
from schema_context import ALLOWED_TABLES

# Path to the read-only service account key, used only for LOCAL development.
# When deployed on Streamlit Community Cloud, this file won't exist -
# credentials come from st.secrets instead (see get_client() below).
CREDENTIALS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "credentials", "bigquery-key.json"
)

# TODO: replace with your actual GCP project ID and BigQuery dataset name
PROJECT_ID = "healthcare-claims-cvs"
DATASET = "healthcare_analytics"  # confirmed: this is where the 3 mart tables actually live


class QueryExecutionError(Exception):
    """Raised when BigQuery fails to run the query (bad syntax, timeout, etc.)."""
    pass


def get_client() -> bigquery.Client:
    """
    Builds a BigQuery client authenticated with the read-only service account.

    Checks Streamlit secrets first (used when deployed on Streamlit Community
    Cloud), and falls back to the local JSON key file (used for local
    development, where st.secrets isn't configured).
    """
    scopes = ["https://www.googleapis.com/auth/bigquery"]

    if "gcp_service_account" in st.secrets:
        # Deployed environment: credentials come from Streamlit secrets,
        # stored as a TOML-parsed dict, not a file on disk.
        credentials_info = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=scopes
        )
    else:
        # Local development: read from the gitignored local JSON key file.
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )

    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


def qualify_table_names(sql: str) -> str:
    """
    BigQuery's Python client requires fully-qualified table names
    (project.dataset.table) - it doesn't assume a default dataset the way
    the BigQuery web UI does. Rather than relying on the LLM to remember to
    write fully-qualified names every time (unreliable), we rewrite the
    SQL here in code, right before execution.

    Only rewrites names that are in our approved ALLOWED_TABLES whitelist -
    this piggybacks on the same whitelist guardrails.py already enforces.
    """
    def replacer(match):
        keyword, table_name = match.group(1), match.group(2).strip("`")
        if table_name in ALLOWED_TABLES:
            return f"{keyword} `{PROJECT_ID}.{DATASET}.{table_name}`"
        return match.group(0)  # leave anything unexpected untouched

    return re.sub(r"(FROM|JOIN)\s+`?([a-zA-Z0-9_]+)`?", replacer, sql, flags=re.IGNORECASE)


def run_query(sql: str):
    """
    Executes the given SQL against BigQuery and returns the results as a
    pandas DataFrame.

    Raises QueryExecutionError with a clean message if the query fails -
    callers should catch this rather than letting a raw BigQuery
    traceback reach the user.
    """
    client = get_client()
    qualified_sql = qualify_table_names(sql)

    try:
        query_job = client.query(qualified_sql)  # starts the query job
        results = query_job.result()             # waits for it to finish, fetches results
        return results.to_dataframe()
    except Exception as e:
        raise QueryExecutionError(f"Query failed to execute: {e}") from e


if __name__ == "__main__":
    # Manual test - run a simple, known-safe query directly against BigQuery
    # to confirm the connection and credentials work before wiring this
    # into the full ask() pipeline.
    test_sql = f"SELECT * FROM `{PROJECT_ID}.{DATASET}.mart_claims_summary` LIMIT 5"

    print(f"Running test query:\n{test_sql}\n")
    try:
        df = run_query(test_sql)
        print("SUCCESS. Results:")
        print(df)
    except QueryExecutionError as e:
        print(f"FAILED: {e}")