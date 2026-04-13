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
    
    updated = 0
    blinkit_po = quotation.items[0].blinkit_po
    if not blinkit_po:
        return
    blinkit_po_data = frappe.get_doc("Blinkit PO Data", blinkit_po)
    po_data = json.loads(blinkit_po_data.po_data)
    po_items_by_line = {
            item["line_number"]: item for item in po_data.get("item_data", [])
        }
    for row in quotation.items:
        po_item = po_items_by_line.get(row.blinkit_po_line_number, {})

        new_item_code = get_item_code(po_item, quotation.party_name)

        if row.item_code != new_item_code:
            row.item_code = new_item_code
            updated += 1

    if updated:
        quotation.run_method("set_price_list_and_item_details")
        quotation.run_method("calculate_taxes_and_totals")
        quotation.save()

    return f"{updated} item(s) updated based on latest Item master"