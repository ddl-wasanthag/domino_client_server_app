import streamlit as st
import requests
import json
from typing import List, Dict

# Configure Streamlit page
st.set_page_config(
    page_title="Domino Test App",
    page_icon="🚀",
    layout="wide"
)

# Backend URL - adjust based on your Domino setup
# In Domino, the backend typically runs on localhost:8000
BACKEND_URL = "http://localhost:8000"

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_items():
    """Fetch items from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/items")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def create_item(name: str, price: float):
    """Create new item"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/items",
            json={"name": name, "price": price}
        )
        return response.status_code == 200
    except:
        return False

def delete_item(item_id: int):
    """Delete item"""
    try:
        response = requests.delete(f"{BACKEND_URL}/api/items/{item_id}")
        return response.status_code == 200
    except:
        return False

def get_random_quote():
    """Get random quote from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/random-quote")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    st.title("🚀 Domino Test Application")
    st.markdown("**Streamlit Frontend + FastAPI Backend**")
    
    # Check backend status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Backend Status")
    with col2:
        if check_backend_health():
            st.success("Backend Online")
        else:
            st.error("Backend Offline")
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
                # Use markdown for quote styling (compatible with older Streamlit)
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
            "Backend Port": "8000 (FastAPI)",
            "Environment": "Domino Platform"
        }
        
        for key, value in config_info.items():
            st.write(f"- **{key}**: {value}")
        
        # Test backend connection
        if st.button("Test Backend Connection"):
            with st.spinner("Testing connection..."):
                try:
                    response = requests.get(f"{BACKEND_URL}/")
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Backend connection successful!")
                        st.json(data)
                    else:
                        st.error(f"❌ Backend returned status: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")

if __name__ == "__main__":
    main()