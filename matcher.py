# matcher.py
import os
import pandas as pd
from extractor import extract_text_from_pdf, parse_invoice_fields

def run_batch_audit():
    po_master = pd.read_csv("data/sap_po_master.csv")
    vault_dir = "data/pdf_vault"
    
    extracted_records = []
    for file in os.listdir(vault_dir):
        if file.endswith(".pdf"):
            path = os.path.join(vault_dir, file)
            raw_text = extract_text_from_pdf(path)
            extracted_records.append(parse_invoice_fields(raw_text))
            
    extracted_df = pd.DataFrame(extracted_records)
    merged = pd.merge(extracted_df, po_master, on="po_number", how="inner")
    
    audit_trail = []
    for _, row in merged.iterrows():
        gstin_match = row['extracted_gstin'] == row['vendor_gstin']
        price_variance = abs(row['extracted_taxable'] - row['po_taxable']) > 0.01
        
        if not gstin_match:
            status = "BLOCK_VENDOR_MISMATCH"
        elif price_variance:
            status = "BLOCK_PRICE_VARIANCE"
        else:
            status = "AUTO_POST_READY"
            
        audit_trail.append({
            "invoice_number": row['invoice_number'],
            "po_number": row['po_number'],
            "invoiced_total": row['extracted_total'],
            "po_total": row['po_total'],
            "matching_status": status
        })
        
    audit_df = pd.DataFrame(audit_trail)
    audit_df.to_csv("data/erp_matching_audit_trail.csv", index=False)
    print("✅ Step 4 Complete: Batch 3-Way reconciliation written to data/erp_matching_audit_trail.csv")

if __name__ == "__main__":
    run_batch_audit()