# Domino Backend (FastAPI)

FastAPI backend service designed to run as a separate Domino App.

## Domino App Prerequisites

Before deploying this app, ensure the following settings are enabled in Domino:

1. **Enable Secure App Identity Propagation** - Required for JWT token-based authentication between Domino apps
2. **Enable Deeplinking and Querying** - Required for cross-app API communication

These settings can be configured in the Domino Admin settings or per-app settings.

## Architecture

```
┌─────────────────────────┐
│   Domino Backend App    │
│   (FastAPI on 8888)     │
│                         │
│  /health                │
│  /api/items             │
│  /api/random-quote      │
└─────────────────────────┘
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
| GET | `/` | Root - service status |
| GET | `/health` | Health check |
| GET | `/api/items` | List all items |
| POST | `/api/items` | Create new item |
| DELETE | `/api/items/{item_id}` | Delete item |
| GET | `/api/random-quote` | Get random quote |

## Domino Deployment

### 1. Create a new Domino Project
- Create a new project for the backend
- Push these files to the project repository

### 2. Create Domino App
- Go to **Publish > App**
- Set the app script to: `app.sh`
- The app will run on port 8888 (Domino requirement)

### 3. Environment Variables (Optional)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins (default: `*`)
- `PORT`: Port to run on (default: `8888`)

### 4. Get the App URL
Once published, note the app URL (e.g., `https://your-domino-instance.com/app/backend-project-name`)
This URL will be used by the frontend to connect.

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

The API will be available at `http://localhost:8888`
