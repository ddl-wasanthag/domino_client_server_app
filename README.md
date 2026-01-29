# Clinical Trial Assistant - Domino POC

A proof-of-concept application demonstrating a Streamlit frontend and FastAPI backend running as separate Domino Apps, with Claude AI integration and AWS RDS database connectivity.

## Architecture

```
┌─────────────────────────┐         ┌─────────────────────────┐
│  Domino Frontend App    │  HTTP   │   Domino Backend App    │
│  (Streamlit)            │────────▶│   (FastAPI)             │
│                         │  +JWT   │                         │
│  - Chat Interface       │         │  ┌───────────────────┐  │
│  - Trial Browser        │         │  │   Claude API      │  │
│  - Natural Language Q&A │         │  │   (SQL + Answer)  │  │
└─────────────────────────┘         │  └───────────────────┘  │
                                    │           │             │
                                    │  ┌───────────────────┐  │
                                    │  │   AWS RDS         │  │
                                    │  │   (PostgreSQL)    │  │
                                    │  └───────────────────┘  │
                                    └─────────────────────────┘
```

## Features

- **Natural Language Queries** - Ask questions about clinical trials in plain English
- **AI-Powered SQL Generation** - Claude generates SQL queries from natural language
- **Clinical Trial Data** - Vision and Immunology trial data with patients and adverse events
- **Secure Cross-App Communication** - JWT token authentication between Domino apps
- **REST API Endpoints** - Standard API endpoints for integration with other applications

## Project Structure

```
domino_client_server_app/
├── domino_backend/          # FastAPI backend (separate Domino project)
│   ├── app.py               # API with Claude AI + database integration
│   ├── app.sh               # Domino app startup script
│   ├── requirements.txt
│   └── README.md
│
├── domino_frontend/         # Streamlit frontend (separate Domino project)
│   ├── app.py               # Chat interface for clinical trial queries
│   ├── app.sh               # Domino app startup script
│   ├── requirements.txt
│   └── README.md
│
├── setup_database.py        # Script to create and populate database
├── INFRASTRUCTURE.md        # AWS infrastructure setup documentation
└── README.md                # This file
```

## Domino App Prerequisites

Before deploying, ensure the following settings are enabled in Domino:

1. **Enable Secure App Identity Propagation** - Required for JWT token-based authentication
2. **Enable Deeplinking and Querying** - Required for cross-app API communication

## Deployment

### 1. Database Setup

See `INFRASTRUCTURE.md` for AWS RDS setup, or run:

```bash
pip install psycopg2-binary
python setup_database.py
```

### 2. Backend Deployment

1. Create a new Domino project with contents of `domino_backend/`
2. Set environment variables:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
   DB_USER=your-db-username
   DB_PASSWORD=your-db-password
   ```
3. Create Domino App using `app.sh`

### 3. Frontend Deployment

1. Create a new Domino project with contents of `domino_frontend/`
2. Set environment variables:
   ```
   BACKEND_URL=https://your-domino-instance.com/apps/app-backend
   ```
3. Create Domino App using `app.sh`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service status |
| GET | `/health` | Health check with DB and Claude status |
| POST | `/api/query` | Natural language query with AI response |
| GET | `/api/trials` | List all clinical trials |
| GET | `/api/trials/{id}/summary` | Detailed trial summary |

## Example Queries

- "How many patients are enrolled in each trial?"
- "What are the most common adverse events?"
- "Show patient demographics for the Uveitis study"
- "Compare adverse event rates across treatment arms"
- "List all severe adverse events in ophthalmology trials"

## Sample Data

The database contains:

| Data | Count | Description |
|------|-------|-------------|
| Clinical Trials | 5 | Vision and Immunology trials (Phase 2/3) |
| Patients | 513 | Randomized across treatment arms |
| Adverse Events | 294 | Mild, Moderate, and Severe events |

### Trials

- IMM-2024-001: Uveitis Treatment Study
- VIS-2023-042: Diabetic Retinopathy Prevention
- IMM-2024-015: Rheumatoid Arthritis Biologic
- VIS-2024-008: Age-Related Macular Degeneration
- IMM-2023-089: Psoriasis IL-17 Inhibitor

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI, Uvicorn
- **AI**: Claude API (Anthropic)
- **Database**: PostgreSQL (AWS RDS)
- **Platform**: Domino Data Lab

## Future Enhancements

- Graph Database integration (Neo4J)
- Starburst connectivity for enterprise data
- SSO/QSID-based user authentication for data access control
- Additional REST API endpoints for external application integration
