# pdf_builder.py
import pandas as pd
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def compile_invoice_pdf(row, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'InvoiceTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor("#1A365D")
    )
    
    story.append(Paragraph(f"INVOICE REFERENCE: {row['invoice_number']}", title_style))
    story.append(Spacer(1, 15))
    
    # Metadata Block Matrix
    meta_data = [
        [Paragraph(f"<b>Vendor Name:</b> {row['vendor_name']}", styles['Normal']), 
         Paragraph(f"<b>Invoice Date:</b> {row['invoice_date']}", styles['Normal'])],
        [Paragraph(f"<b>GSTIN:</b> {row['vendor_gstin']}", styles['Normal']), 
         Paragraph(f"<b>PO Reference:</b> {row['po_number']}", styles['Normal'])]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    story.append(meta_table)
    story.append(Spacer(1, 25))
    
    # Financial Block Table
    rupee = "₹ "
    taxable = float(row['taxable_amount'])
    total = float(row['total_amount'])
    gst_split = round((total - taxable) / 2, 2)
    
    fin_data = [
        ["Line Description", "Category Type", "Amount Value"],
        ["Commercial Operations Fulfillment", "Taxable Amount", f"{rupee}{taxable:,.2f}"],
        ["Central GST (9%)", "CGST", f"{rupee}{gst_split:,.2f}"],
        ["State GST (9%)", "SGST", f"{rupee}{gst_split:,.2f}"],
        ["Total Settlement Due", "Total Amount", f"{rupee}{total:,.2f}"]
    ]
    
    fin_table = Table(fin_data, colWidths=[240, 140, 140])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(fin_table)
    doc.build(story)

if __name__ == "__main__":
    df = pd.read_csv("data/simulated_invoice_runs.csv")
    for _, row in df.iterrows():
        compile_invoice_pdf(row, f"data/pdf_vault/{row['invoice_number']}.pdf")
    print(f"✅ Step 2 Complete: Built {len(df)} production-styled PDFs inside data/pdf_vault/")