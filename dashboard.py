# dashboard.py
import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(page_title="AP Operations Dashboard", layout="wide")
st.title("🛡️ Accounts Payable Audit & Automation Gateway")

layout_left, layout_right = st.columns([1, 2])

with layout_left:
    st.header("📥 Ingest Document File")
    uploaded = st.file_uploader("Upload Vendor Invoice PDF", type=["pdf"])
    
    if uploaded is not None:
        with st.spinner("Processing through API gateway integration..."):
            files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
            try:
                res = requests.post("http://127.0.0.1:8000/api/v1/invoice/process", files=files)
                if res.status_code == 200:
                    output = res.json()
                    status = output["status"]
                    
                    if status == "AUTO_POST_READY":
                        st.success("✅ AUTO-POST READY")
                    elif status == "BLOCK_PRICE_VARIANCE":
                        st.error(f"❌ {status}")
                    else:
                        st.warning(f"⚠️ {status}")
                        
                    st.write(f"**System Note:** {output['audit_note']}")
                    st.json(output["comparison"])
                else:
                    st.error(f"Gateway connection error: {res.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("API Gateway unreachable. Verify app.py is active on port 8000.")

with layout_right:
    st.header("📊 Global Batch Settlement Logs")
    log_path = "data/erp_matching_audit_trail.csv"
    
    if os.path.exists(log_path):
        df = pd.read_csv(log_path)
        
        tot = len(df)
        passed = len(df[df["matching_status"] == "AUTO_POST_READY"])
        st_rate = (passed / tot) * 100 if tot > 0 else 0
        
        stat1, stat2 = st.columns(2)
        stat1.metric("Straight-Through Processing Rate", f"{st_rate:.1f}%")
        stat2.metric("Total Batch Logs Ingested", f"{tot} items")
        
        st.write("### Active Audit Matrix Logs")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Run matcher.py first to build baseline log tables.")