# Domino Test Application

A simple client/server application with Streamlit frontend and FastAPI backend, designed for Domino Apps platform.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │
│   Frontend      │───▶│    Backend      │
│   (port 8888)   │    │   (port 8000)   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                   │
            ┌─────────────┐
            │   Nginx     │
            │ Reverse     │
            │   Proxy     │
            └─────────────┘
                   │
            ┌─────────────┐
            │ Kubernetes  │
            │    Pod      │
            └─────────────┘
```

## Files Structure

```
domino-test-app/
├── app.py              # Streamlit frontend
├── main.py             # FastAPI backend
├── requirements.txt    # Python dependencies
├── app.sh              # Domino app Startup script
└── README.md          # This file
```

## Features

### Frontend (Streamlit)
- **Items Manager**: Create, view, and delete items
- **Random Quote Generator**: Get inspirational quotes
- **System Info**: View configuration and test backend connection
- **Health Check**: Monitor backend status

### Backend (FastAPI)
- RESTful API endpoints
- CORS enabled for frontend communication
- Health check endpoint
- Items CRUD operations
- Random quote service

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/items` - List all items
- `POST /api/items` - Create new item
- `DELETE /api/items/{item_id}` - Delete item
- `GET /api/random-quote` - Get random quote

## Setup Instructions

### 1. Create the files
Save each file in your Domino project:
- `app.py` - Streamlit frontend
- `main.py` - FastAPI backend  
- `requirements.txt` - Dependencies
- `app.sh` - Startup script

### 2. Make the startup script executable
Create a Domino APP from the app.sh

## Usage

Once deployed on Domino Apps:

1. Access the app through the Domino Apps interface
2. Use the **Items Manager** to add/remove items
3. Generate random quotes in the **Random Quote** tab
4. Check system status in the **System Info** tab
