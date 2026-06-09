# Updated snippet for dashboard.py file processing logic
import streamlit as st
import pandas as pd
import os
from extractor import extract_text_from_pdf, parse_invoice_fields

# ... (rest of your layout code) ...

if uploaded is not None:
    st.info("Processing document using native cloud processing engine...")
    
    # Save uploaded file temporarily on the cloud container
    with open(uploaded.name, "wb") as f:
        f.write(uploaded.getbuffer())
        
    # Execute extraction and matching logic natively on the server instance
    text = extract_text_from_pdf(uploaded.name)
    extracted = parse_invoice_fields(text)
    
    # Run the 3-Way match rules against the master data
    df = pd.read_csv("data/sap_po_master.csv")
    po_record = df[df["po_number"] == extracted.get("po_number")]
    
    if not po_record.empty:
        erp = po_record.iloc[0]
        gstin_match = extracted["extracted_gstin"] == erp["vendor_gstin"]
        price_variance = abs(extracted["extracted_taxable"] - erp["po_taxable"]) > 0.01
        
        if not gstin_match:
            st.error("❌ BLOCK_VENDOR_MISMATCH: Vendor identity does not match ERP Master File!")
        elif price_variance:
            st.warning("⚠️ BLOCK_PRICE_VARIANCE: Invoiced pricing deviates from original PO limit.")
        else:
            st.success("✅ AUTO_POST_READY: 3-Way match cleared successfully.")
            st.balloons()
            
        st.json({"Extracted Data": extracted, "ERP Reference": erp.to_dict()})
    else:
        st.error(f"PO Reference {extracted.get('po_number')} not found in ERP Master File.")
        
    # Clean up file copy
    os.remove(uploaded.name)