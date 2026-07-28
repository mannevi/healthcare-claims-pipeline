"""
Phase 5: Streamlit UI

A simple web interface for the NL -> SQL -> Guardrails -> BigQuery pipeline.
Run with: streamlit run app.py
"""

import streamlit as st
from nl_to_sql_gemini import ask
from guardrails import GuardrailViolation
from execute_query import QueryExecutionError

st.set_page_config(page_title="Healthcare Claims AI Analyst", page_icon="🏥")

st.title("🏥 Healthcare Claims AI Analyst")
st.caption("Ask questions about Medicare claims data in plain English. "
           "Powered by a schema-grounded NL-to-SQL pipeline with safety guardrails.")

# Example questions as clickable buttons - helps first-time visitors
# understand what the tool can do without having to guess.
st.write("**Try an example:**")
example_questions = [
    "Which state had the highest total paid amount?",
    "What are the top 5 most expensive diagnosis codes by average cost per claim?",
    "Which provider has the lowest payment ratio percentage?",
]

# Track the question in session state so a button click and manual typing
# both flow through the same variable.
if "question" not in st.session_state:
    st.session_state.question = ""

cols = st.columns(len(example_questions))
for col, example in zip(cols, example_questions):
    if col.button(example, use_container_width=True):
        st.session_state.question = example

question = st.text_input(
    "Or ask your own question:",
    value=st.session_state.question,
    placeholder="e.g. Which state had the highest total paid amount?",
)

if st.button("Ask", type="primary") and question:
    with st.spinner("Generating SQL, validating, and querying BigQuery..."):
        try:
            safe_sql, results_df = ask(question)

            st.success("Query completed")

            st.subheader("Answer")
            st.dataframe(results_df, use_container_width=True)

            with st.expander("SQL used"):
                st.code(safe_sql, language="sql")

        except GuardrailViolation as e:
            st.error(f"Blocked by safety guardrails: {e}")

        except QueryExecutionError as e:
            st.error(f"Query execution failed: {e}")

        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.divider()
st.caption(
    "This assistant can only read from 3 approved tables (mart_claims_summary, "
    "mart_provider_performance, mart_diagnosis_cost_analysis) via a read-only "
    "BigQuery service account. It cannot modify or delete any data."
)