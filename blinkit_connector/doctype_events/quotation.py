import frappe
from blinkit_connector.blinkit_repository import BlinkitRepository

def before_submit(doc, method=None):
    if doc.blinkit_edi_order and frappe.db.get_value("Blinkit PO Data", doc.blinkit_po, "sync_doc") == doc.name:
        BlinkitRepository().acknowledge_po(doc.blinkit_po)