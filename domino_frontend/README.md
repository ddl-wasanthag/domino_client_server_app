# Domino Frontend (Streamlit)

Streamlit frontend application designed to run as a separate Domino App, connecting to the backend service.

## Domino App Prerequisites

Before deploying this app, ensure the following settings are enabled in Domino:

1. **Enable Secure App Identity Propagation** - Required for JWT token-based authentication between Domino apps
2. **Enable Deeplinking and Querying** - Required for cross-app API communication

These settings can be configured in the Domino Admin settings or per-app settings.

## Architecture

```
┌─────────────────────────┐         ┌─────────────────────────┐
│  Domino Frontend App    │  HTTP   │   Domino Backend App    │
│  (Streamlit on 8888)    │────────▶│   (FastAPI on 8888)     │
│                         │         │                         │
│  - Items Manager        │         │  - /api/items           │
│  - Random Quote         │         │  - /api/random-quote    │
│  - System Info          │         │  - /health              │
└─────────────────────────┘         └─────────────────────────┘
```

## Files

```
domino_frontend/
├── app.py           # Streamlit application
├── app.sh           # Domino app startup script
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Features

- **Items Manager**: Create, view, and delete items
- **Random Quote Generator**: Get inspirational quotes from backend
- **System Info**: View configuration and test backend connection
- **Health Check**: Monitor backend status

## Domino Deployment

### 1. Create a new Domino Project
- Create a new project for the frontend
- Push these files to the project repository

### 2. Configure Environment Variables
Set the following environment variable in Domino:
- `BACKEND_URL`: URL of the backend Domino app
  - Example: `https://your-domino-instance.com/app/backend-project-name`

### 3. Create Domino App
- Go to **Publish > App**
- Set the app script to: `app.sh`
- The app will run on port 8888 (Domino requirement)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_URL` | URL of the FastAPI backend app | `http://localhost:8888` |

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set backend URL (if backend is running elsewhere)
export BACKEND_URL="http://localhost:8888"

# Run the app
streamlit run app.py --server.port 8888
```

The UI will be available at `http://localhost:8888`

## Connecting to Backend

The frontend connects to the backend via the `BACKEND_URL` environment variable.
Make sure to:
1. Deploy the backend app first
2. Get the backend app URL from Domino
3. Set `BACKEND_URL` in the frontend project's environment variables
