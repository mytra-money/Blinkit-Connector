import frappe

def after_insert(doc, method=None):
    if any(i.get("blinkit_po") for i in doc.items):
        blinkit_po = doc.items[0].blinkit_po
        if not doc.po_no:
            doc.po_no = frappe.db.get_value("Blinkit PO Data", {"name": blinkit_po}, fieldname="po_number")
    
def before_submit(doc, method=None):
    if any(i.get("blinkit_po") for i in doc.items):
        #submit ack if sync doc is sales order
        return