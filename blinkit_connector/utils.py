import frappe
import json

class utils:
    def __init__(self, data):
        self.data = frappe._dict(data)
    
    def sync_order(self):
        data = self.data
        if data.get("event_name") == "PO_CREATION":
            blinkit_po_data = frappe.new_doc("Blinkit PO Data")
            blinkit_po_data.po_number = data.get("purchase_order_details").get("purchase_order_number")
            blinkit_po_data.po_data = frappe.as_json(data, indent=4)
            blinkit_po_data.insert(ignore_permissions=True)
            return "success"
        else:
            frappe.log_error("Incorrect Blinkit request")
            frappe.local.response['http_status_code'] = 417
            frappe.throw("Incorrect Blinkit Request")

@frappe.whitelist()
def refresh_blinkit_items(quotation):
    quotation = frappe.get_doc("Quotation", quotation)
    if quotation.docstatus != 0:
        frappe.throw("Can only refresh Draft Quotations")

    blinkit_setting = frappe.get_cached_doc("Blinkit Setting")

    def get_item_code(order_item, customer_name) -> str:
        ean = order_item.get("upc")
        buyer_ref_code = order_item.get("item_id")
        item_code_with_ean = frappe.db.get_value(
            "Item Barcode",
            filters={"barcode_type": "EAN", "barcode": ean, "parenttype": "Item"},
            fieldname="parent"
        )
        item_code_with_buyer_ref = frappe.db.get_value(
            "Item Customer Detail",
            filters={"customer_name": customer_name, "ref_code": buyer_ref_code, "parenttype": "Item"},
            fieldname="parent"
        )
        if item_code_with_ean:
            return item_code_with_ean
        elif item_code_with_buyer_ref:
            return item_code_with_buyer_ref
        else:
            return blinkit_setting.default_item
    
    blinkit_po = quotation.items[0].blinkit_po
    if not blinkit_po:
        return
    blinkit_po_data = frappe.get_doc("Blinkit PO Data", blinkit_po)
    po_data = json.loads(blinkit_po_data.po_data)
    order_items = po_data.get("item_data")
    quotation.items = []
    for item in order_items:
        item_details = {
            "item_code": get_item_code(item, quotation.party_name),
            "customer_item_code": item.get("item_id"),
            "qty": item.get("units_ordered"),
            "uom": "Nos",
            "rate": item.get("cost_price"),
            "conversion_factor": 1.0,
            "blinkit_po_line_number": item.get("line_number"),
            "blinkit_po": blinkit_po_data
        }
        quotation.append("items", item_details)
    quotation.taxes_and_charges = None
    quotation.set("taxes", [])
    quotation.run_method("set_missing_lead_customer_details")
    quotation.run_method("set_price_list_and_item_details")
    quotation.run_method("calculate_taxes_and_totals")
    quotation.payment_schedule = []
    quotation.save()

    return f"Item(s) updated based on latest Item master"