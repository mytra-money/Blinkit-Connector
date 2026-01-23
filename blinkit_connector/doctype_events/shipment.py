import frappe

def validate(doc, method=None):
    delivery_notes = list(set(row.delivery_note for row in doc.shipment_delivery_note))
    if len(delivery_notes):
        delivery_note_si_rows = frappe.get_all(
            "Delivery Note Item",
            fields=["against_sales_invoice"],
            filters=[["parent", "in", delivery_notes],["docstatus", "=", 1]]
        )
        delivery_note_sales_invoices = {row.against_sales_invoice for row in delivery_note_si_rows if row.against_sales_invoice}
        sales_invoice_items = frappe.get_all(
            "Sales Invoice Item",
            fields=["parent"],
            filters=[["delivery_note", "in", delivery_notes],["docstatus", "=", 1]]
        )
        sales_invoices_delivery_note = {row.parent for row in sales_invoice_items if row.parent}
        sales_invoices = delivery_note_sales_invoices.union(sales_invoices_delivery_note)
        for s in sales_invoices:
            sales_invoice = frappe.get_cached_doc("Sales Invoice", s)
            blinkit_po = sales_invoice.items[0].blinkit_po
            if blinkit_po:
                doc.append("blinkit_invoice", {"sales_invoice": sales_invoice.name, "sent_blinkit_asn": 0})