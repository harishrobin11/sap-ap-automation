import os
import shutil
import pandas as pd
import streamlit as st
from extractor import extract_text_from_pdf, parse_invoice_fields

# 1. Page Configuration & UI Title
st.set_page_config(page_title="ERP AP Core Integration Gateway", page_icon="🏦", layout="wide")
st.title("🏦 ERP AP Core Integration Gateway")
st.subheader("Automated 3-Way Invoice Matcher & Ledger Validation")

PO_MASTER_PATH = "data/sap_po_master.csv"
UPLOAD_DIR = "data/api_uploads"

# Ensure directories exist locally inside the container
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 2. File Upload UI Component (Replaces FastAPI's UploadFile endpoint)
uploaded_file = st.file_uploader("Upload Vendor Invoice (PDF format only)", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Processing invoice and executing validation rules..."):
        
        # Save the uploaded file locally to read it
        save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file, buffer)
            
        # Execution of text extraction pipeline
        try:
            text = extract_text_from_pdf(save_path)
            extracted = parse_invoice_fields(text)
        except Exception as e:
            st.error(f"Failed to parse PDF pipeline layout: {str(e)}")
            st.stop()
        
        # 3. Check for PO Number
        po_num = extracted.get("po_number")
        if not po_num:
            st.error("❌ Transaction REJECTED")
            st.warning("Reason: No PO code detected in document body.")
            st.json(extracted)
            st.stop()
            
        # 4. Read Master ERP Database
        if not os.path.exists(PO_MASTER_PATH):
            st.error(f"Critical System Error: Master registry data file missing at '{PO_MASTER_PATH}'")
            st.stop()
            
        df = pd.read_csv(PO_MASTER_PATH)
        po_record = df[df["po_number"] == po_num]
        
        if po_record.empty:
            st.error("❌ Transaction REJECTED")
            st.warning(f"Reason: PO {po_num} does not exist in master registry.")
            st.json(extracted)
            st.stop()
            
        erp = po_record.iloc[0]
        
        # 5. Match Valuation Logic
        gstin_match = extracted["extracted_gstin"] == erp["vendor_gstin"]
        price_variance = abs(extracted["extracted_taxable"] - erp["po_taxable"]) > 0.01
        
        # Generate Evaluation Output UI
        st.markdown("---")
        st.subheader("📋 Audit Summary Results")
        
        if not gstin_match:
            st.error("🚨 Status: BLOCK_VENDOR_MISMATCH")
            st.info("💡 Note: Extracted vendor authentication token deviates from approved master file.")
        elif price_variance:
            st.error("🚨 Status: BLOCK_PRICE_VARIANCE")
            st.info("💡 Note: Invoice pricing deviates from authorized purchase contract limit.")
        else:
            st.success("✅ Status: AUTO_POST_READY")
            st.balloons()
            st.info("💡 Note: 3-Way Match verified. Transaction ready for automated ledger posting.")
            
        # 6. Structured Metric Comparison Display
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="Invoice Invoice Number", value=str(extracted["invoice_number"]))
            st.metric(label="PO Reference Match Link", value=str(po_num))
            
        with col2:
            st.metric(
                label="Taxable Amount (Invoice vs ERP)", 
                value=f"${extracted['extracted_taxable']:.2f}", 
                delta=f"ERP Limit: ${erp['po_taxable']:.2f}",
                delta_color="normal" if not price_variance else "inverse"
            )
            
        # Raw Data Comparison Table block
        st.subheader("📊 System Sync Details")
        comparison_df = pd.DataFrame({
            "Metric/Field": ["Taxable Amount", "GSTIN Token Identity"],
            "Extracted From Invoice": [extracted['extracted_taxable'], extracted['extracted_gstin']],
            "Allowed by ERP Master File": [erp['po_taxable'], erp['vendor_gstin']],
            "Status Match": ["✅ Match" if not price_variance else "❌ Mismatch", "✅ Match" if gstin_match else "❌ Mismatch"]
        })
        st.table(comparison_df)
