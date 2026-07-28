"""
Phase 2: Core NL -> SQL engine (no guardrails yet - that's Phase 3)

Uses Google Gemini's free API tier - no credit card needed.

Demonstrates:
  - System prompt vs user prompt separation
  - Low temperature for deterministic SQL generation
  - Grounding the model using the schema context from Phase 1
"""

import os
from google import genai
from google.genai import types
from schema_context import build_schema_context
from guardrails import validate_and_prepare, GuardrailViolation
from execute_query import run_query, QueryExecutionError

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT_TEMPLATE = """You are a SQL analyst for a Medicare healthcare claims database on BigQuery.

You may ONLY generate SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.

You may ONLY reference the following tables and columns. Do not invent table or column names
that are not listed here:

{schema_context}

Rules:
- Return ONLY the raw SQL query. No explanation, no markdown code fences, no commentary.
- Always include a LIMIT clause (default LIMIT 100) unless the question clearly asks for an aggregate
  that returns a single row (e.g. "what is the total paid amount").
- Use standard BigQuery SQL syntax.
"""


def generate_sql(question: str) -> str:
    """
    Takes a plain-English question, returns a SQL query string.
    This is the function that turns "grounding" + "system/user prompt"
    concepts into actual working code.
    """
    schema_context = build_schema_context()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(schema_context=schema_context)

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=question,                    # <-- the actual question, changes every call
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,  # <-- standing instructions + grounding
            temperature=0,                     # deterministic - same question should give same query
            max_output_tokens=1024,            # raised - thinking tokens share this budget
            thinking_config=types.ThinkingConfig(thinking_level="minimal"),  # simple task, no need for deep reasoning
        ),
    )

    sql = response.text.strip()

    # Small cleanup in case the model wraps it in a code fence anyway
    if sql.startswith("```"):
        sql = sql.strip("`")
        sql = sql.replace("sql\n", "", 1) if sql.startswith("sql\n") else sql

    return sql.strip()


def ask(question: str):
    """
    Full pipeline: generate SQL -> validate it -> execute it -> return real results.

    Raises GuardrailViolation if the generated SQL fails any safety check.
    Raises QueryExecutionError if BigQuery fails to run the (approved) query.
    Callers must NOT proceed past either exception (fail closed).

    Returns a tuple: (safe_sql, results_dataframe)
    """
    raw_sql = generate_sql(question)
    safe_sql = validate_and_prepare(raw_sql)   # raises GuardrailViolation if unsafe
    results_df = run_query(safe_sql)           # raises QueryExecutionError if it fails
    return safe_sql, results_df


if __name__ == "__main__":
    # Manual test loop - now runs the full pipeline end-to-end, including
    # real BigQuery execution.
    test_questions = [
        "Which state had the highest total paid amount?",
        "What are the top 5 most expensive diagnosis codes by average cost per claim?",
        "Which provider has the lowest payment ratio percentage?",
    ]

    for q in test_questions:
        print(f"\nQuestion: {q}")
        try:
            safe_sql, results_df = ask(q)
            print(f"SQL used:\n{safe_sql}")
            print(f"\nResults:\n{results_df}")
        except GuardrailViolation as e:
            print(f"BLOCKED by guardrails: {e}")
        except QueryExecutionError as e:
            print(f"EXECUTION FAILED: {e}")