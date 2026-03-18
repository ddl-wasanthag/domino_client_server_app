#!/bin/bash

# Start script for Domino Apps — Pharma Clinical Data Platform
# Launches FastAPI backend (port 8000) and Streamlit frontend (port 8888).
#
# To point the API at a Domino Dataset instead of the bundled ./data directory:
#   export DATA_DIR=/domino/datasets/local/<your-dataset>

echo "Starting Pharma Clinical Data Platform..."

# ------------------------------------------------------------------
# Streamlit configuration
# ------------------------------------------------------------------
echo "Writing Streamlit config..."
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml << 'EOF'
[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"
serverPort = 8888

[server]
port = 8888
enableCORS = false
enableXsrfProtection = false
maxMessageSize = 250
EOF

# ------------------------------------------------------------------
# FastAPI backend
# ------------------------------------------------------------------
echo "Starting FastAPI backend on port 8000..."
python main.py &
BACKEND_PID=$!

# Give uvicorn a moment to bind the port
sleep 3

# ------------------------------------------------------------------
# Streamlit frontend
# ------------------------------------------------------------------
echo "Starting Streamlit frontend on port 8888..."
streamlit run app.py &
FRONTEND_PID=$!

# ------------------------------------------------------------------
# Graceful shutdown
# ------------------------------------------------------------------
shutdown() {
    echo "Shutting down services..."
    kill "$BACKEND_PID" 2>/dev/null
    kill "$FRONTEND_PID" 2>/dev/null
    exit 0
}

trap shutdown SIGTERM SIGINT

echo "Both services started."
echo "  Backend  PID : $BACKEND_PID"
echo "  Frontend PID : $FRONTEND_PID"
echo "  DATA_DIR     : ${DATA_DIR:-$(pwd)/data}"
echo "Access the app through the Domino Apps interface."

wait
