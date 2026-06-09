# extractor.py
import re
import pdfplumber

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "".join([page.extract_text() + "\n" for page in pdf.pages if page.extract_text()])

def parse_invoice_fields(text):
    """Regex pipeline handling broken font-substitutions dynamically."""
    po_match = re.search(r"PO\sReference:\s*([A-Z0-9-]+)", text, re.IGNORECASE)
    inv_match = re.search(r"INVOICE\sREFERENCE:\s*([A-Z0-9-]+)", text, re.IGNORECASE)
    date_match = re.search(r"Invoice\sDate:\s*(\d{2}-[A-Za-z]{3}-\d{4})", text)
    gstin_match = re.search(r"GSTIN:\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", text)
    
    # Financial fields: strips out thousands commas and handles the corrupted font mapping 'n'
    taxable_match = re.search(r"Taxable\s+Amount\s+(?:n|Rs\.?|\s)*([\d,]+\.\d{2})", text, re.IGNORECASE)
    total_match = re.search(r"Total\s+Amount\s+(?:n|Rs\.?|\s)*([\d,]+\.\d{2})", text, re.IGNORECASE)

    return {
        "invoice_number": inv_match.group(1).strip() if inv_match else None,
        "po_number": po_match.group(1).strip() if po_match else None,
        "invoice_date": date_match.group(1).strip() if date_match else None,
        "extracted_gstin": gstin_match.group(1).strip() if gstin_match else None,
        "extracted_taxable": float(taxable_match.group(1).replace(",", "")) if taxable_match else 0.0,
        "extracted_total": float(total_match.group(1).replace(",", "")) if total_match else 0.0,
    }