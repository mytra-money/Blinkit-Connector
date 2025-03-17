import frappe
from blinkit_connector.blinkit_repository import BlinkitRepository

def before_submit(doc, method=None):
    if any(i.get("blinkit_po") for i in doc.items):
        blinkit_po = doc.items[0].blinkit_po
        BlinkitRepository().acknowledge_po(blinkit_po)