import frappe
from blinkit_connector.blinkit_repository import BlinkitRepository

def before_submit(doc, method=None):
    if any(i.get("blinkit_po") for i in doc.items):
        blinkit_po = doc.items[0].blinkit_po
        sync_doc, sync_doc_name = frappe.db.get_value("Blinkit PO Data", blinkit_po, ["sync_via", "sync_doc"])
        if  sync_doc == "Quotation" and sync_doc_name == doc.name:
            BlinkitRepository().acknowledge_po(blinkit_po)