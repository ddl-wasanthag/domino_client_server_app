#!/bin/bash

# Domino App startup script for FastAPI backend
# Domino Apps with UI must run on port 8888

echo "Starting FastAPI Backend on Domino..."

# Run FastAPI with uvicorn on port 8888
python app.py
