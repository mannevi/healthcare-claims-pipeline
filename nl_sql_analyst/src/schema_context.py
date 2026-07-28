"""
Phase 1: Schema Context (Grounding)

Reads the dbt schema.yml and builds a compact, LLM-friendly text block
describing ONLY the 3 mart tables we want the assistant to query.

We deliberately do NOT expose stg_claims / int_claims_deduplicated —
those are staging/intermediate tables, not business-ready.
"""

import yaml

# Only these tables are ever shown to the LLM.
# This whitelist is used again later in Phase 3 (guardrails) to validate
# that the generated SQL doesn't reference anything outside this list.
ALLOWED_TABLES = {
    "mart_claims_summary",
    "mart_provider_performance",
    "mart_diagnosis_cost_analysis",
}

# Manually curated column types + one-line meanings, based on the actual
# mart SQL models (schema.yml only has a few columns documented, so we
# fill in the rest here by reading the .sql model definitions).
MART_DEFINITIONS = {
    "mart_claims_summary": {
        "description": "Monthly claims summary by state and diagnosis.",
        "columns": {
            "claim_month": "STRING - Month of claim, format YYYY-MM",
            "state": "STRING - Provider state code",
            "diagnosis_code": "STRING - ICD-10 diagnosis code",
            "diagnosis_description": "STRING - Human-readable diagnosis name",
            "diagnosis_category": "STRING - High-level diagnosis category",
            "total_claims": "INTEGER - Number of claims in this group",
            "total_paid": "FLOAT - Total amount paid by Medicare",
            "total_charged": "FLOAT - Total amount originally charged",
            "avg_paid_per_claim": "FLOAT - Average paid amount per claim",
            "total_denied_amount": "FLOAT - Total charged minus total paid (denied/unpaid portion)",
        },
    },
    "mart_provider_performance": {
        "description": "Provider-level cost and performance analysis.",
        "columns": {
            "provider_id": "STRING - Unique provider identifier",
            "npi_number": "STRING - National Provider Identifier",
            "provider_state": "STRING - State the provider is located in",
            "total_claims": "INTEGER - Number of claims filed by this provider",
            "total_paid": "FLOAT - Total amount paid to this provider",
            "total_charged": "FLOAT - Total amount this provider charged",
            "payment_ratio_pct": "FLOAT - (total_paid / total_charged) * 100",
            "avg_claim_paid": "FLOAT - Average paid amount per claim",
            "max_claim": "FLOAT - Largest single claim paid",
            "min_claim": "FLOAT - Smallest single claim paid",
        },
    },
    "mart_diagnosis_cost_analysis": {
        "description": "Cost analysis grouped by diagnosis code.",
        "columns": {
            "diagnosis_code": "STRING - ICD-10 diagnosis code",
            "diagnosis_description": "STRING - Human-readable diagnosis name",
            "diagnosis_category": "STRING - High-level diagnosis category",
            "claim_count": "INTEGER - Number of claims with this diagnosis",
            "total_cost": "FLOAT - Total amount paid across all claims with this diagnosis",
            "avg_cost_per_claim": "FLOAT - Average paid amount per claim",
            "max_claim": "FLOAT - Largest single claim for this diagnosis",
            "min_claim": "FLOAT - Smallest single claim for this diagnosis",
            "cost_stddev": "FLOAT - Standard deviation of claim cost (spread/variability)",
        },
    },
}


def load_schema_descriptions(schema_yml_path: str) -> dict:
    """
    Optional: pull the human-written table/column `description` fields out of
    the real dbt schema.yml, so descriptions stay in sync with what you
    actually documented there instead of living twice in two files.
    """
    with open(schema_yml_path, "r") as f:
        raw = yaml.safe_load(f)

    descriptions = {}
    for model in raw.get("models", []):
        name = model.get("name")
        if name not in ALLOWED_TABLES:
            continue
        descriptions[name] = {
            "description": model.get("description", ""),
            "columns": {
                c["name"]: c.get("description", "")
                for c in model.get("columns", [])
            },
        }
    return descriptions


def build_schema_context() -> str:
    """
    Builds the grounding text block injected into the system prompt.
    This is the concrete answer to: "what does the LLM actually see about my database?"
    """
    blocks = []
    for table_name, definition in MART_DEFINITIONS.items():
        lines = [f"Table: {table_name}", f"Description: {definition['description']}", "Columns:"]
        for col_name, col_desc in definition["columns"].items():
            lines.append(f"  - {col_name}: {col_desc}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


if __name__ == "__main__":
    # Quick manual check — run this file directly to see exactly what
    # gets fed to the LLM as grounding context.
    print(build_schema_context())