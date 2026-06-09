# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
import pandas as pd
from extractor import extract_text_from_pdf, parse_invoice_fields

app = FastAPI(title="ERP AP Core Integration Gateway")
PO_MASTER_PATH = "data/sap_po_master.csv"

@app.post("/api/v1/invoice/process")
async def process_invoice(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads supported.")
        
    save_path = os.path.join("data/api_uploads", file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Execution
    text = extract_text_from_pdf(save_path)
    extracted = parse_invoice_fields(text)
    
    po_num = extracted.get("po_number")
    if not po_num:
        return {"status": "REJECTED", "reason": "No PO code detected in document body.", "data": extracted}
        
    df = pd.read_csv(PO_MASTER_PATH)
    po_record = df[df["po_number"] == po_num]
    
    if po_record.empty:
        return {"status": "REJECTED", "reason": f"PO {po_num} does not exist in master registry.", "data": extracted}
        
    erp = po_record.iloc[0]
    
    # Match Valuation Logic
    gstin_match = extracted["extracted_gstin"] == erp["vendor_gstin"]
    price_variance = abs(extracted["extracted_taxable"] - erp["po_taxable"]) > 0.01
    
    if not gstin_match:
        decision = "BLOCK_VENDOR_MISMATCH"
        note = "Extracted vendor authentication token deviates from approved master file."
    elif price_variance:
        decision = "BLOCK_PRICE_VARIANCE"
        note = f"Invoice pricing deviates from authorized purchase contract limit."
    else:
        decision = "AUTO_POST_READY"
        note = "3-Way Match verified. Transaction ready for automated ledger posting."
        
    return {
        "invoice_number": extracted["invoice_number"],
        "po_reference": po_num,
        "status": decision,
        "audit_note": note,
        "comparison": {
            "invoice_taxable": extracted["extracted_taxable"],
            "erp_allowed_taxable": erp["po_taxable"],
            "invoice_gstin": extracted["extracted_gstin"],
            "erp_allowed_gstin": erp["vendor_gstin"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)