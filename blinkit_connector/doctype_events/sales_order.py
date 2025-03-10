import frappe

def after_insert(doc, method=None):
    if doc.blinkit_edi_order:
        if not doc.po_no:
            doc.po_no = frappe.db.get_value("Blinkit PO Data", {"name": doc.blinkit_po}, fieldname="po_number")
    
def before_submit(doc, method=None):
    if doc.blinkit_edi_order:
        #submit ack if sync doc is sales order
        return