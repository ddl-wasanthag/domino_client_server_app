import streamlit as st
import requests
import os
from typing import Optional
import urllib3

# Suppress SSL warnings for internal Domino communication
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure Streamlit page
st.set_page_config(
    page_title="Clinical Trial Assistant",
    page_icon="🔬",
    layout="wide"
)

# Backend URL - configured via environment variable
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8888")
DOMINO_TOKEN_ENDPOINT = "http://localhost:8899/access-token"


def get_domino_token() -> Optional[str]:
    """Fetch the user's JWT token from Domino's local token endpoint."""
    try:
        response = requests.get(DOMINO_TOKEN_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return None
    except:
        return None


def get_auth_headers() -> dict:
    """Get authorization headers with Domino JWT token."""
    token = get_domino_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def check_backend_health():
    """Check backend health status."""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BACKEND_URL}/health", headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return True, response.json()
        return False, {"error": f"Status {response.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}


def get_trials():
    """Fetch all clinical trials."""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BACKEND_URL}/api/trials", headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def query_clinical_data(question: str):
    """Send a natural language query to the backend."""
    try:
        headers = get_auth_headers()
        headers["Content-Type"] = "application/json"
        response = requests.post(
            f"{BACKEND_URL}/api/query",
            headers=headers,
            json={"question": question},
            timeout=60,
            verify=False
        )
        if response.status_code == 200:
            return response.json()
        return {"error": f"Error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def get_trial_summary(trial_id: str):
    """Get detailed summary for a trial."""
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{BACKEND_URL}/api/trials/{trial_id}/summary",
            headers=headers,
            timeout=10,
            verify=False
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def main():
    st.title("🔬 Clinical Trial Assistant")
    st.markdown("*AI-powered insights for Vision and Immunology clinical trials*")

    # Sidebar - System Status
    with st.sidebar:
        st.header("System Status")
        is_healthy, health_info = check_backend_health()

        if is_healthy:
            st.success("Backend: Online")
            st.info(f"Database: {health_info.get('database', 'unknown')}")
            db_counts = health_info.get('db_counts', {})
            if db_counts:
                st.caption(f"Trials: {db_counts.get('trials', 0)} | Patients: {db_counts.get('patients', 0)} | AEs: {db_counts.get('adverse_events', 0)}")
            st.info(f"Claude API: {health_info.get('claude_api', 'unknown')}")
        else:
            st.error("Backend: Offline")
            st.code(str(health_info))
            st.stop()

        st.divider()
        st.header("Available Trials")
        trials = get_trials()
        if trials:
            for trial in trials:
                with st.expander(f"{trial['trial_id']}"):
                    st.write(f"**{trial['name']}**")
                    st.write(f"Phase: {trial['phase']}")
                    st.write(f"Area: {trial['therapeutic_area']}")
                    st.write(f"Status: {trial['status']}")
                    st.write(f"Patients: {trial['patient_count']}")

    # Main content - Chat Interface
    st.header("Ask a Question")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sql_query" in message and message["sql_query"]:
                with st.expander("View SQL Query"):
                    st.code(message["sql_query"], language="sql")

    # Example questions
    st.markdown("**Example questions:**")
    example_cols = st.columns(2)
    examples = [
        "How many patients are enrolled in each trial?",
        "What are the most common adverse events?",
        "Show patient demographics for the Uveitis study",
        "Compare adverse event rates across treatment arms"
    ]

    for i, example in enumerate(examples):
        col = example_cols[i % 2]
        if col.button(example, key=f"example_{i}", use_container_width=True):
            st.session_state.pending_question = example
            st.rerun()

    # Check for pending question from example buttons
    if "pending_question" in st.session_state:
        prompt = st.session_state.pending_question
        del st.session_state.pending_question
    else:
        prompt = st.chat_input("Ask about clinical trials, patients, or adverse events...")

    # Process the question
    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing clinical trial data..."):
                result = query_clinical_data(prompt)

            if "error" in result:
                st.error(result["error"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error: {result['error']}"
                })
            else:
                st.markdown(result["answer"])

                if result.get("sql_query"):
                    with st.expander("View SQL Query"):
                        st.code(result["sql_query"], language="sql")

                if result.get("data_summary"):
                    st.caption(result["data_summary"])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sql_query": result.get("sql_query")
                })

    # Clear chat button
    if st.session_state.messages:
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    main()
