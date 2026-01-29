import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
import anthropic

app = FastAPI(title="Clinical Trial API", version="2.0.0")

# Configure CORS
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration - all values from environment variables
DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "dbname": os.environ.get("DB_NAME", "clinicaltrials"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
}

# Claude API configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


# Pydantic models
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sql_query: Optional[str] = None
    data_summary: Optional[str] = None


class TrialInfo(BaseModel):
    trial_id: str
    name: str
    phase: str
    therapeutic_area: str
    status: str
    patient_count: int


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def get_database_schema():
    """Get the database schema for context."""
    return """
Database Schema:

Table: clinical_trials
- trial_id (VARCHAR): Primary key, e.g., 'IMM-2024-001'
- name (VARCHAR): Trial name
- phase (VARCHAR): 'Phase 1', 'Phase 2', 'Phase 3'
- therapeutic_area (VARCHAR): e.g., 'Immunology', 'Ophthalmology', 'Immunology/Ophthalmology'
- start_date (DATE): Trial start date
- status (VARCHAR): 'Active', 'Recruiting', 'Completed'
- sponsor (VARCHAR): Sponsoring company

Table: patients
- patient_id (VARCHAR): Primary key, e.g., 'PAT-00001'
- trial_id (VARCHAR): Foreign key to clinical_trials
- age (INTEGER): Patient age
- gender (VARCHAR): 'Male' or 'Female'
- treatment_arm (VARCHAR): Treatment group, e.g., 'Placebo', 'Low Dose', 'High Dose'
- enrollment_date (DATE): Date enrolled
- site_id (VARCHAR): Clinical site, e.g., 'SITE-US-001'

Table: adverse_events
- event_id (SERIAL): Primary key
- patient_id (VARCHAR): Foreign key to patients
- event_type (VARCHAR): e.g., 'Headache', 'Nausea', 'Eye irritation'
- severity (VARCHAR): 'Mild', 'Moderate', 'Severe'
- event_date (DATE): Date of event
- resolved (BOOLEAN): Whether resolved
- description (TEXT): Event description
"""


def execute_sql_query(sql: str) -> list:
    """Execute a SQL query and return results."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        # Convert to plain dicts and handle special types
        clean_results = []
        for row in results:
            clean_row = {}
            for key, value in dict(row).items():
                # Convert date objects to strings
                if hasattr(value, 'isoformat'):
                    clean_row[key] = value.isoformat()
                else:
                    clean_row[key] = value
            clean_results.append(clean_row)
        return clean_results
    finally:
        conn.close()


def query_with_claude(question: str) -> QueryResponse:
    """Use Claude to interpret the question, generate SQL, and provide an answer."""
    # Re-read env var each time in case it was set after startup
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)
    schema = get_database_schema()

    # Step 1: Generate SQL query
    sql_prompt = f"""You are a SQL expert. Given the following database schema and question, generate a PostgreSQL query to answer the question.

{schema}

Question: {question}

Rules:
1. Only generate SELECT queries (no INSERT, UPDATE, DELETE)
2. Return ONLY the SQL query, no explanation
3. Use appropriate JOINs when needed
4. Limit results to 100 rows maximum
5. If the question cannot be answered with SQL, return "NO_SQL_NEEDED"

SQL Query:"""

    sql_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": sql_prompt}]
    )

    sql_query = sql_response.content[0].text.strip()

    # Clean up SQL - remove markdown code blocks if present
    if sql_query.startswith("```"):
        # Remove markdown code blocks
        lines = sql_query.split("\n")
        # Remove first line (```sql) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        sql_query = "\n".join(lines).strip()

    # Execute SQL if valid
    data_results = []
    data_summary = None

    if sql_query and sql_query != "NO_SQL_NEEDED" and "SELECT" in sql_query.upper():
        try:
            print(f"[DEBUG] Executing SQL: {sql_query}")
            data_results = execute_sql_query(sql_query)
            data_summary = f"Query returned {len(data_results)} rows"
            print(f"[DEBUG] Results: {len(data_results)} rows")
        except Exception as e:
            data_summary = f"SQL Error: {str(e)}"
            sql_query = f"Error in query: {sql_query}"
            print(f"[DEBUG] SQL Error: {str(e)}")

    # Step 2: Generate natural language answer
    answer_prompt = f"""You are a helpful clinical trials assistant. Answer the following question based on the database schema and query results.

{schema}

Question: {question}

SQL Query Used: {sql_query}

Query Results (showing up to 20 rows):
{str(data_results[:20]) if data_results else "No data retrieved"}

Please provide a clear, concise answer to the question. If there's data, summarize the key findings. Be specific with numbers and details from the results."""

    answer_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": answer_prompt}]
    )

    answer = answer_response.content[0].text.strip()

    return QueryResponse(
        question=question,
        answer=answer,
        sql_query=sql_query if sql_query != "NO_SQL_NEEDED" else None,
        data_summary=data_summary
    )


# ============== API Endpoints ==============

@app.get("/")
async def root():
    return {
        "message": "Clinical Trial API is running on Domino!",
        "version": "2.0.0",
        "features": ["Database connectivity", "Claude AI integration", "Natural language queries"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = "healthy"
    db_counts = {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Actually query the data to verify tables exist and have data
        cursor.execute("SELECT COUNT(*) FROM clinical_trials")
        db_counts["trials"] = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) FROM patients")
        db_counts["patients"] = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) FROM adverse_events")
        db_counts["adverse_events"] = cursor.fetchone()["count"]
        conn.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Re-read env var in case it was set after app startup
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    claude_status = "configured" if api_key else "not configured"

    # Debug: show if key exists (masked)
    key_debug = f"key starts with: {api_key[:20]}..." if api_key else "no key found"

    return {
        "status": "healthy",
        "service": "clinical-trial-api",
        "database": db_status,
        "db_counts": db_counts,
        "claude_api": claude_status,
        "key_debug": key_debug
    }


@app.post("/api/query", response_model=QueryResponse)
async def query_clinical_data(request: QueryRequest):
    """
    Natural language query endpoint.
    Send a question about clinical trials and get an AI-powered answer.
    """
    try:
        return query_with_claude(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trials", response_model=List[TrialInfo])
async def get_trials():
    """Get all clinical trials with patient counts."""
    sql = """
        SELECT
            ct.trial_id,
            ct.name,
            ct.phase,
            ct.therapeutic_area,
            ct.status,
            COUNT(p.patient_id) as patient_count
        FROM clinical_trials ct
        LEFT JOIN patients p ON ct.trial_id = p.trial_id
        GROUP BY ct.trial_id, ct.name, ct.phase, ct.therapeutic_area, ct.status
        ORDER BY ct.trial_id
    """
    try:
        results = execute_sql_query(sql)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trials/{trial_id}/summary")
async def get_trial_summary(trial_id: str):
    """Get detailed summary for a specific trial."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get trial info
        cursor.execute("SELECT * FROM clinical_trials WHERE trial_id = %s", (trial_id,))
        trial = cursor.fetchone()

        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found")

        # Get patient demographics
        cursor.execute("""
            SELECT
                gender,
                COUNT(*) as count,
                AVG(age) as avg_age,
                treatment_arm
            FROM patients
            WHERE trial_id = %s
            GROUP BY gender, treatment_arm
        """, (trial_id,))
        demographics = cursor.fetchall()

        # Get adverse events summary
        cursor.execute("""
            SELECT
                ae.event_type,
                ae.severity,
                COUNT(*) as count
            FROM adverse_events ae
            JOIN patients p ON ae.patient_id = p.patient_id
            WHERE p.trial_id = %s
            GROUP BY ae.event_type, ae.severity
            ORDER BY count DESC
            LIMIT 10
        """, (trial_id,))
        adverse_events = cursor.fetchall()

        conn.close()

        return {
            "trial": dict(trial),
            "demographics": [dict(d) for d in demographics],
            "top_adverse_events": [dict(ae) for ae in adverse_events]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8888))
    uvicorn.run(app, host="0.0.0.0", port=port)
