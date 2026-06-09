# generator.py
import os
import random
import pandas as pd
from datetime import datetime, timedelta

class EnterpriseDataGenerator:
    def __init__(self, num_vendors=5, seed=42):
        random.seed(seed)
        self.vendors = self._generate_master_vendors(num_vendors)
        
    def _generate_master_vendors(self, count):
        """Generates realistic Enterprise Vendor Master Records."""
        vendors = []
        states = ["29", "27", "33", "07", "19"]  # KA, MH, TN, DL, WB
        pan_chars = "ABCDE"
        
        for i in range(count):
            name = f"{random.choice(['Alpha', 'Beta', 'Quantum', 'Nexus', 'Vertex'])} Solutions Pvt Ltd"
            state = random.choice(states)
            pan = f"{''.join(random.choices(pan_chars, k=5))}{random.randint(1000, 9999)}F"
            gstin = f"{state}{pan}1Z{random.choice('0123456789AZ')}"
            
            vendors.append({
                "vendor_id": f"VND-{10000 + i}",
                "vendor_name": name,
                "vendor_gstin": gstin,
                "base_tax_rate": 0.18  # 18% Standard GST
            })
        return vendors

    def generate_po_and_invoice_pairs(self, count=10):
        """Generates matching transactional records with targeted compliance deviations."""
        po_records = []
        invoice_records = []
        start_date = datetime(2026, 1, 1)
        
        for i in range(count):
            vendor = random.choice(self.vendors)
            po_id = f"PO-{4500000000 + i}"  # SAP standard PO number sequences
            inv_id = f"INV-{800000 + i}"
            
            # Base pricing logistics
            quantity = random.randint(20, 100)
            unit_price = round(random.uniform(200.0, 800.0), 2)
            po_taxable = round(quantity * unit_price, 2)
            po_total = round(po_taxable * 1.18, 2)
            po_date = start_date + timedelta(days=random.randint(1, 30))
            
            po_records.append({
                "po_number": po_id,
                "vendor_id": vendor["vendor_id"],
                "vendor_gstin": vendor["vendor_gstin"],
                "po_taxable": po_taxable,
                "po_total": po_total
            })
            
            # Scenario Distribution
            anomaly_type = "CLEAN"
            inv_taxable = po_taxable
            inv_total = po_total
            inv_gstin = vendor["vendor_gstin"]
            
            dice = random.random()
            if dice < 0.20:
                anomaly_type = "PRICE_VARIANCE"
                inv_taxable = round(po_taxable * random.uniform(1.05, 1.15), 2)  # Overcharge
                inv_total = round(inv_taxable * 1.18, 2)
            elif dice < 0.40:
                anomaly_type = "VENDOR_MISMATCH"
                inv_gstin = f"29XXXXX{random.randint(1000,9999)}X1Z0"  # Fraudulent GSTIN
            
            inv_date = po_date + timedelta(days=random.randint(2, 7))
            
            invoice_records.append({
                "invoice_number": inv_id,
                "po_number": po_id,
                "vendor_name": vendor["vendor_name"],
                "vendor_gstin": inv_gstin,
                "invoice_date": inv_date.strftime("%d-%b-%Y"),
                "taxable_amount": inv_taxable,
                "total_amount": inv_total,
                "anomaly_label": anomaly_type
            })
            
        return pd.DataFrame(po_records), pd.DataFrame(invoice_records)

if __name__ == "__main__":
    gen = EnterpriseDataGenerator()
    po_df, inv_df = gen.generate_po_and_invoice_pairs(15)
    os.makedirs("data", exist_ok=True)
    po_df.to_csv("data/sap_po_master.csv", index=False)
    inv_df.to_csv("data/simulated_invoice_runs.csv", index=False)
    print("✅ Step 1 Complete: ERP relational data written to data/ directory.")