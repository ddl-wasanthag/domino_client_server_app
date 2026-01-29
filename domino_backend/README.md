# Domino Backend - Clinical Trial API

FastAPI backend service with Claude AI integration and PostgreSQL database connectivity.

## Domino App Prerequisites

Before deploying this app, ensure the following settings are enabled in Domino:

1. **Enable Secure App Identity Propagation** - Required for JWT token-based authentication between Domino apps
2. **Enable Deeplinking and Querying** - Required for cross-app API communication

## Architecture

```
┌─────────────────────────────────────┐
│      Domino Backend App             │
│      (FastAPI on port 8888)         │
│                                     │
│   ┌─────────────┐   ┌─────────────┐ │
│   │ Claude API  │   │  AWS RDS    │ │
│   │ (Anthropic) │   │ PostgreSQL  │ │
│   └─────────────┘   └─────────────┘ │
│         │                 │         │
│         ▼                 ▼         │
│   ┌─────────────────────────────┐   │
│   │     Natural Language        │   │
│   │     Query Processing        │   │
│   │  1. Generate SQL from query │   │
│   │  2. Execute against DB      │   │
│   │  3. Summarize with AI       │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Files

```
domino_backend/
├── app.py           # FastAPI application
├── app.sh           # Domino app startup script
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service status and features |
| GET | `/health` | Health check (DB counts, Claude API status) |
| POST | `/api/query` | Natural language query with AI response |
| GET | `/api/trials` | List all clinical trials with patient counts |
| GET | `/api/trials/{trial_id}/summary` | Detailed trial summary with demographics and AEs |

### POST /api/query

Send a natural language question about clinical trials:

**Request:**
```json
{
  "question": "What are the most common adverse events?"
}
```

**Response:**
```json
{
  "question": "What are the most common adverse events?",
  "answer": "Based on the data, the most common adverse events are...",
  "sql_query": "SELECT event_type, COUNT(*) as count FROM adverse_events GROUP BY event_type ORDER BY count DESC",
  "data_summary": "Query returned 8 rows"
}
```

### GET /api/trials

**Response:**
```json
[
  {
    "trial_id": "IMM-2024-001",
    "name": "Uveitis Treatment Study",
    "phase": "Phase 3",
    "therapeutic_area": "Immunology/Ophthalmology",
    "status": "Active",
    "patient_count": 88
  }
]
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `DB_HOST` | PostgreSQL host | Yes |
| `DB_USER` | Database username | Yes |
| `DB_PASSWORD` | Database password | Yes |
| `DB_PORT` | PostgreSQL port | No (default: 5432) |
| `DB_NAME` | Database name | No (default: clinicaltrials) |
| `PORT` | App port | No (default: 8888) |
| `ALLOWED_ORIGINS` | CORS origins | No (default: *) |

## Deployment

### 1. Create Domino Project
Push these files to a new Domino project repository.

### 2. Set Environment Variables
In Domino project settings, add:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_USER=your-db-username
DB_PASSWORD=your-db-password
```

### 3. Create Domino App
- Go to **Publish > App**
- Set the app script to: `app.sh`
- Enable required prerequisites (see above)

## Database Schema

The backend connects to a PostgreSQL database with three tables:

**clinical_trials**
- `trial_id` (PK), `name`, `phase`, `therapeutic_area`, `start_date`, `status`, `sponsor`

**patients**
- `patient_id` (PK), `trial_id` (FK), `age`, `gender`, `treatment_arm`, `enrollment_date`, `site_id`

**adverse_events**
- `event_id` (PK), `patient_id` (FK), `event_type`, `severity`, `event_date`, `resolved`, `description`

## Local Testing

```bash
export ANTHROPIC_API_KEY="your-api-key"
pip install -r requirements.txt
python app.py
```

The API will be available at `http://localhost:8888`
