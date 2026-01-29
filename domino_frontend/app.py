import streamlit as st
import requests
import os
from typing import List, Dict, Optional
import urllib3

# Suppress SSL warnings for internal Domino communication
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure Streamlit page
st.set_page_config(
    page_title="Domino Test App",
    page_icon="🚀",
    layout="wide"
)

# Backend URL - configured via environment variable for separate Domino projects
# Set BACKEND_URL to your backend Domino app URL (e.g., https://your-domino-instance/app/backend-app)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8888")

# Domino token endpoint (available within Domino apps)
DOMINO_TOKEN_ENDPOINT = "http://localhost:8899/access-token"


def get_domino_token() -> Optional[str]:
    """Fetch the user's JWT token from Domino's local token endpoint"""
    try:
        response = requests.get(DOMINO_TOKEN_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return None
    except Exception as e:
        print(f"[DEBUG] Failed to get Domino token: {e}")
        return None


def get_auth_headers() -> dict:
    """Get authorization headers with Domino JWT token"""
    token = get_domino_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def check_backend_health():
    """Check if backend is running"""
    try:
        url = f"{BACKEND_URL}/health"
        headers = get_auth_headers()
        print(f"[DEBUG] Attempting to connect to: {url}")
        print(f"[DEBUG] Using auth: {'Yes' if headers else 'No'}")
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response body: {response.text}")
        if response.status_code == 200:
            return True, f"Status: {response.status_code}, Body: {response.text[:500]}"
        else:
            return False, f"Status: {response.status_code}, Body: {response.text[:500]}"
    except Exception as e:
        import traceback
        error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"[DEBUG] Error: {error_details}")
        return False, error_details

def get_items():
    """Fetch items from backend"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BACKEND_URL}/api/items", headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def create_item(name: str, price: float):
    """Create new item"""
    try:
        headers = get_auth_headers()
        response = requests.post(
            f"{BACKEND_URL}/api/items",
            headers=headers,
            json={"name": name, "price": price},
            timeout=10,
            verify=False
        )
        return response.status_code == 200
    except:
        return False

def delete_item(item_id: int):
    """Delete item"""
    try:
        headers = get_auth_headers()
        response = requests.delete(f"{BACKEND_URL}/api/items/{item_id}", headers=headers, timeout=10, verify=False)
        return response.status_code == 200
    except:
        return False

def get_random_quote():
    """Get random quote from backend"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BACKEND_URL}/api/random-quote", headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    st.title("🚀 Domino Test Application")
    st.markdown("**Streamlit Frontend + FastAPI Backend (Separate Domino Projects)**")

    # Debug section - always visible
    with st.expander("🔍 Debug Information", expanded=True):
        st.code(f"BACKEND_URL = {BACKEND_URL}")

        # Check token availability
        token = get_domino_token()
        if token:
            st.success(f"Domino JWT token obtained (length: {len(token)})")
        else:
            st.warning("No Domino JWT token available (running locally?)")

        st.write("Testing connection...")
        is_healthy, response_info = check_backend_health()
        if is_healthy:
            st.success("Backend is reachable!")
        else:
            st.error("Backend is NOT reachable")
        # Always show response info
        if response_info:
            st.code(response_info)

    # Check backend status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Backend Status")
    with col2:
        if is_healthy:
            st.success("Backend Online")
        else:
            st.error("Backend Offline")

    if not is_healthy:
        st.warning(f"Backend URL: {BACKEND_URL}")
        if response_info:
            st.error(f"Details: {response_info}")
        st.stop()

    # Create tabs for different features
    tab1, tab2, tab3 = st.tabs(["📝 Items Manager", "💭 Random Quote", "🔧 System Info"])

    with tab1:
        st.subheader("Items Management")

        # Add new item form
        with st.form("add_item_form"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                item_name = st.text_input("Item Name", placeholder="Enter item name")
            with col2:
                item_price = st.number_input("Price", min_value=0.01, step=0.01)
            with col3:
                st.write("")  # Spacer
                submitted = st.form_submit_button("Add Item")

        if submitted and item_name:
            if create_item(item_name, item_price):
                st.success(f"Added '{item_name}' successfully!")
                st.rerun()
            else:
                st.error("Failed to add item")

        # Display items
        items = get_items()
        if items:
            st.subheader("Current Items")
            for item in items:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{item['name']}**")
                with col2:
                    st.write(f"${item['price']:.2f}")
                with col3:
                    if st.button("Delete", key=f"del_{item['id']}"):
                        if delete_item(item['id']):
                            st.success("Item deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete item")
        else:
            st.info("No items found. Add some items above!")

    with tab2:
        st.subheader("Random Quote Generator")

        if st.button("Get Random Quote", type="primary"):
            quote_data = get_random_quote()
            if quote_data:
                st.markdown(f"> *{quote_data['quote']}*")
                st.markdown(f"**— {quote_data['author']}**")
            else:
                st.error("Failed to fetch quote")

    with tab3:
        st.subheader("System Information")

        # Display configuration
        st.write("**Configuration:**")
        config_info = {
            "Backend URL": BACKEND_URL,
            "Frontend Port": "8888 (Streamlit)",
            "Backend Port": "8888 (FastAPI - separate Domino App)",
            "Environment": "Domino Platform - Separate Projects"
        }

        for key, value in config_info.items():
            st.write(f"- **{key}**: {value}")

        # Test backend connection
        if st.button("Test Backend Connection"):
            with st.spinner("Testing connection..."):
                try:
                    headers = get_auth_headers()
                    response = requests.get(f"{BACKEND_URL}/", headers=headers, timeout=10, verify=False)
                    if response.status_code == 200:
                        data = response.json()
                        st.success("Backend connection successful!")
                        st.json(data)
                    else:
                        st.error(f"Backend returned status: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")

if __name__ == "__main__":
    main()
