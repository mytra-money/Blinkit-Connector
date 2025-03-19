import frappe
from blinkit_connector.blinkit_repository import BlinkitRepository

def after_insert(doc, method=None):
    if any(i.get("blinkit_po") for i in doc.items):
        blinkit_po = doc.items[0].blinkit_po
        if not doc.po_no:
            doc.po_no = frappe.db.get_value("Blinkit PO Data", {"name": blinkit_po}, fieldname="po_number")
            doc.save()
    
def before_submit(doc, method=None):
    if any(i.get("blinkit_po") for i in doc.items):
        blinkit_po = doc.items[0].blinkit_po
        sync_doc, sync_doc_name = frappe.db.get_value("Blinkit PO Data", blinkit_po, ["sync_via", "sync_doc"])
        if  sync_doc == "Sales Order" and sync_doc_name == doc.name:
            BlinkitRepository().acknowledge_po(blinkit_po)