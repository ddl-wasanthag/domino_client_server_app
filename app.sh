#!/bin/bash

# Start script for Domino Apps following Domino's Streamlit configuration pattern
# This script starts both FastAPI backend and Streamlit frontend

echo "Starting Domino Test Application..."

# Create Streamlit configuration directory and config file (Domino pattern)
echo "Setting up Streamlit configuration..."
mkdir -p ~/.streamlit
echo "[browser]" > ~/.streamlit/config.toml
echo "gatherUsageStats = true" >> ~/.streamlit/config.toml
echo "serverAddress = \"0.0.0.0\"" >> ~/.streamlit/config.toml
echo "serverPort = 8888" >> ~/.streamlit/config.toml
echo "[server]" >> ~/.streamlit/config.toml
echo "port = 8888" >> ~/.streamlit/config.toml
echo "enableCORS = false" >> ~/.streamlit/config.toml
echo "enableXsrfProtection = false" >> ~/.streamlit/config.toml
echo "maxMessageSize = 250" >> ~/.streamlit/config.toml

# Start FastAPI backend in the background
echo "Starting FastAPI backend on port 8000..."
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Streamlit frontend using Domino's pattern (no CLI args needed with config file)
echo "Starting Streamlit frontend on port 8888..."
streamlit run app.py &
FRONTEND_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap signals for graceful shutdown
trap shutdown SIGTERM SIGINT

echo "Application started successfully!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Streamlit config created at ~/.streamlit/config.toml"
echo "Access the app through Domino Apps interface"

# Wait for both processes
wait