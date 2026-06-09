import streamlit as st
import pandas as pd
import requests
import os


# Fallback to localhost if running locally, otherwise use the live web URL
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000")

# Example API call construction
# response = requests.post(f"{BACKEND_URL}/predict", files=files)
st.set_page_config(page_title="ERP AP Control Center", layout="wide")

st.title("🛡️ Enterprise Accounts Payable Automation Control Center")
st.subheader("Automated Anomaly Detection & Deterministic 3-Way Matching Engine")

# Setup layout blocks
col1, col2 = st.columns([1, 2])

# Sidebar Setup: Operational Metrics
with col1:
    st.header("📥 Ingest Single Document")
    uploaded_file = st.file_uploader("Upload Vendor Invoice PDF", type=["pdf"])
    
    if uploaded_file is not None:
        with st.spinner("Processing through pipeline gateway..."):
            # Forward the file buffer straight to the FastAPI backend service
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            try:
                response = requests.post("http://127.0.0.1:8000/api/v1/invoice/process", files=files)
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("Analysis Complete!")
                    status = result["status"]
                    
                    if status == "AUTO_POST_READY":
                        st.balloons()
                        st.metric(label="System Route Decision", value="✅ AUTO-POST READY")
                    elif status == "BLOCK_PRICE_VARIANCE":
                        st.error(f"❌ {status}")
                    else:
                        st.warning(f"⚠️ {status}")
                        
                    st.write(f"**Audit Note:** {result['audit_note']}")
                    st.json(result["comparison"])
                else:
                    st.error(f"API Error Code: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Connection Error: Is the FastAPI gateway server running on port 8000?")

# Main View Panel: Enterprise Audit Trail Analytics
with col2:
    st.header("📊 Global Batch Settlement Audit Log")
    
    AUDIT_TRAIL_PATH = "data/erp_matching_audit_trail.csv"
    if os.path.exists(AUDIT_TRAIL_PATH):
        df = pd.read_csv(AUDIT_TRAIL_PATH)
        
        # Calculate high-value business KPIs to present during discussions
        total_invoices = len(df)
        auto_posted = len(df[df["matching_status"] == "AUTO_POST_READY"])
        blocked_price = len(df[df["matching_status"] == "BLOCK_PRICE_VARIANCE"])
        blocked_vendor = len(df[df["matching_status"] == "BLOCK_VENDOR_MISMATCH"])
        
        automation_rate = (auto_posted / total_invoices) * 100 if total_invoices > 0 else 0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Straight-Through Processing Rate", f"{automation_rate:.1f}%", help="Percentage of documents clearing matching without manual touch.")
        kpi2.metric("Price Variance Holds", f"{blocked_price} items")
        kpi3.metric("Security Vendor Mismatch Holds", f"{blocked_vendor} items")
        
        st.write("### Production Log Matrix (Simulated Database State)")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No logs located. Run the batch pipeline matching script to populate database state views.")
