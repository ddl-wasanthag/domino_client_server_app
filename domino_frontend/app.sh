#!/bin/bash

# Domino App startup script for Streamlit frontend
# Domino Apps with UI must run on port 8888

echo "Starting Streamlit Frontend on Domino..."

# Create Streamlit configuration directory and config file
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml << EOF
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

# Run Streamlit on port 8888
streamlit run app.py
