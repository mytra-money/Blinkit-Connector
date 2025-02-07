import frappe

def on_submit(doc, method=None):
    if doc.blinkit_edi_order:
        #submit ack if sync doc is quotation
        return