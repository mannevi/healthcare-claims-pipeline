"""
Phase 3: Guardrails

Validates LLM-generated SQL BEFORE it's allowed to run anywhere.
This is enforcement, not instruction - the checks here don't trust
that the model followed the system prompt, they verify it.

Layers (defense in depth):
  1. Keyword blocklist   - reject dangerous statement types outright
  2. Table whitelist      - only our 3 marts may be referenced
  3. Row limit enforcement - add LIMIT if the model forgot one
  4. (Layer 4, read-only DB credentials, is set up outside this code -
     see the README note at the bottom of this file)
"""

import re
from schema_context import ALLOWED_TABLES

# Layer 1: keyword blocklist
# Any of these appearing anywhere in the query = automatic rejection.
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "TRUNCATE", "MERGE", "CREATE", "GRANT", "REVOKE",
]

DEFAULT_ROW_LIMIT = 100


class GuardrailViolation(Exception):
    """Raised when a generated query fails a safety check.
    We fail closed: if this is raised, execution must NOT proceed."""
    pass


def check_dangerous_keywords(sql: str) -> None:
    """Layer 1. Simple, fast, catches the obvious/malicious cases first."""
    upper_sql = sql.upper()
    for keyword in DANGEROUS_KEYWORDS:
        # \b = word boundary, so we match DROP but not e.g. a column named "dropdown"
        if re.search(rf"\b{keyword}\b", upper_sql):
            raise GuardrailViolation(
                f"Blocked: query contains disallowed keyword '{keyword}'. "
                f"Only SELECT statements are permitted."
            )


def check_is_select_only(sql: str) -> None:
    """Layer 1b. The query must actually START with SELECT (or WITH, for CTEs).
    This catches cases where dangerous keywords aren't used, but the
    statement still isn't a plain read query."""
    stripped = sql.strip().upper()
    if not (stripped.startswith("SELECT") or stripped.startswith("WITH")):
        raise GuardrailViolation(
            f"Blocked: query must start with SELECT or WITH. "
            f"Got: '{sql.strip()[:50]}...'"
        )


def check_table_whitelist(sql: str) -> None:
    """Layer 2. Extract anything that looks like a table reference after
    FROM or JOIN, and confirm every one of them is in our approved list.

    Note: this is a pragmatic regex check, not a full SQL parser. It's not
    bulletproof against a determined adversary crafting exotic SQL syntax,
    but combined with Layer 4 (read-only credentials), the worst case is
    still bounded - it can't be tricked into writing data even if a table
    reference somehow slipped past this check.
    """
    # Matches table names after FROM/JOIN, optionally wrapped in backticks
    # and optionally schema-qualified (e.g. project.dataset.table)
    pattern = r"(?:FROM|JOIN)\s+`?([a-zA-Z0-9_.]+)`?"
    matches = re.findall(pattern, sql, flags=re.IGNORECASE)

    if not matches:
        raise GuardrailViolation("Blocked: could not identify any table reference in the query.")

    for raw_table in matches:
        # Strip any project.dataset prefix, keep just the table name
        table_name = raw_table.split(".")[-1]
        if table_name not in ALLOWED_TABLES:
            raise GuardrailViolation(
                f"Blocked: query references table '{table_name}', "
                f"which is not in the approved list: {sorted(ALLOWED_TABLES)}"
            )


def enforce_row_limit(sql: str, default_limit: int = DEFAULT_ROW_LIMIT) -> str:
    """Layer 3. If the model forgot a LIMIT clause, add one ourselves
    rather than trusting it remembered. Returns the (possibly modified) SQL."""
    if re.search(r"\bLIMIT\s+\d+", sql, flags=re.IGNORECASE):
        return sql  # already has one, leave it as-is
    return sql.rstrip().rstrip(";") + f"\nLIMIT {default_limit}"


def validate_and_prepare(sql: str) -> str:
    """
    Main entry point. Runs all layers in order. Fails closed - the moment
    any check fails, a GuardrailViolation is raised and execution must stop.

    Returns the final SQL (with row limit enforced) ONLY if every check passes.
    """
    check_dangerous_keywords(sql)
    check_is_select_only(sql)
    check_table_whitelist(sql)
    safe_sql = enforce_row_limit(sql)
    return safe_sql


if __name__ == "__main__":
    # Manual test cases - run this file directly to see the guardrails
    # catch both a legitimate query and a couple of bad-faith attempts.
    test_cases = [
        # Should PASS
        "SELECT state, total_paid FROM mart_claims_summary ORDER BY total_paid DESC LIMIT 5",
        # Should FAIL - dangerous keyword
        "DELETE FROM mart_claims_summary WHERE state = 'FL'",
        # Should FAIL - prompt injection attempt
        "SELECT * FROM mart_claims_summary; DROP TABLE mart_claims_summary;",
        # Should FAIL - table not in whitelist
        "SELECT * FROM stg_claims LIMIT 10",
        # Should PASS but get a LIMIT added automatically
        "SELECT provider_id, total_paid FROM mart_provider_performance ORDER BY total_paid DESC",
    ]

    for sql in test_cases:
        print(f"\nInput SQL: {sql}")
        try:
            result = validate_and_prepare(sql)
            print(f"PASSED. Final SQL:\n{result}")
        except GuardrailViolation as e:
            print(f"BLOCKED: {e}")

# ---------------------------------------------------------------------------
# Layer 4 (outside this code): read-only BigQuery credentials
#
# Create a BigQuery service account with a role limited to BigQuery Data
# Viewer (or a custom role with only bigquery.tables.getData /
# bigquery.jobs.create) scoped to just the dataset containing your 3 marts.
# This means that even in the worst case - every check above somehow fails
# or is bypassed - the credentials themselves cannot execute a write or
# delete. This is the layer that doesn't depend on your code being perfect.
# ---------------------------------------------------------------------------