# Domino Frontend - Clinical Trial Assistant

Streamlit chat interface for querying clinical trial data using natural language.

## Domino App Prerequisites

Before deploying this app, ensure the following settings are enabled in Domino:

1. **Enable Secure App Identity Propagation** - Required for JWT token-based authentication between Domino apps
2. **Enable Deeplinking and Querying** - Required for cross-app API communication

## Architecture

```
┌───────────────────────────────────────┐
│      Domino Frontend App              │
│      (Streamlit on port 8888)         │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │         Chat Interface          │  │
│  │  - Natural language input       │  │
│  │  - AI-powered responses         │  │
│  │  - SQL query visibility         │  │
│  └─────────────────────────────────┘  │
│                  │                    │
│  ┌─────────────────────────────────┐  │
│  │         Sidebar                 │  │
│  │  - System health status         │  │
│  │  - Trial browser                │  │
│  │  - Database statistics          │  │
│  └─────────────────────────────────┘  │
│                  │                    │
│           JWT Token Auth              │
│      (localhost:8899/access-token)    │
│                  │                    │
│                  ▼                    │
│         Backend API Calls             │
└───────────────────────────────────────┘
```

## Features

- **Natural Language Queries** - Ask questions about clinical trials in plain English
- **AI-Powered Answers** - Claude AI generates SQL and summarizes results
- **Trial Browser** - View all available trials in the sidebar
- **Chat History** - Maintains conversation context within session
- **SQL Visibility** - Optionally view the generated SQL queries
- **Example Questions** - Quick-start buttons for common queries

## Example Questions

- "How many patients are enrolled in each trial?"
- "What are the most common adverse events?"
- "Show patient demographics for the Uveitis study"
- "Compare adverse event rates across treatment arms"
- "List all severe adverse events in ophthalmology trials"
- "What is the average age of patients in Phase 3 trials?"

## Files

```
domino_frontend/
├── app.py           # Streamlit application
├── app.sh           # Domino app startup script
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BACKEND_URL` | URL of the backend Domino app | Yes |

## Deployment

### 1. Deploy Backend First
Ensure the backend app is deployed and note its URL.

### 2. Create Domino Project
Push these files to a new Domino project repository.

### 3. Set Environment Variables
```
BACKEND_URL=https://your-domino-instance.com/apps/app-backend
```

### 4. Create Domino App
- Go to **Publish > App**
- Set the app script to: `app.sh`
- Enable required prerequisites (see above)

## Authentication

The frontend automatically handles authentication for cross-app communication:

1. Obtains JWT token from Domino's local endpoint (`http://localhost:8899/access-token`)
2. Includes token as `Authorization: Bearer` header in all backend requests
3. Enables secure communication between Domino apps

## Local Testing

```bash
export BACKEND_URL="http://localhost:8888"
pip install -r requirements.txt
streamlit run app.py --server.port 8889
```

Note: When running locally, JWT token authentication will not be available. The backend should still work without authentication for local development.

## UI Components

### Sidebar
- **System Status**: Shows backend, database, and Claude API health
- **Data Counts**: Displays number of trials, patients, and adverse events
- **Trial Browser**: Expandable list of all clinical trials with details

### Main Area
- **Example Questions**: Clickable buttons for common queries
- **Chat Input**: Text field for natural language questions
- **Response Display**: AI-generated answers with optional SQL query view
- **Clear History**: Button to reset conversation
