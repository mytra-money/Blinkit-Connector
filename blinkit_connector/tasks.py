import frappe
import json
from frappe.utils.data import (getdate)

@frappe.whitelist()
def hourly():
    create_sales_docs()


def create_sales_docs():
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
    def get_customer_and_billing_details(order_details) -> frappe._dict:
        blinkit_outlet_id = str(order_details.get("grofers_delivery_details", {}).get("grofers_outlet_id"))
        customer_details = frappe._dict({"customer":None, "customer_address":None, "shipping_address":None, "warehouse": None, "billing_address": None})
        for w in blinkit_setting.linked_warehouses:
            if blinkit_outlet_id == w.blinkit_outlet_id:
                customer_details.warehouse = w.warehouse
                customer_details.customer = w.customer
                customer_details.billing_address = w.billing_address
                customer_details.customer_address = w.customer_address
                customer_details.shipping_address = w.shipping_address
                break
        if not customer_details.customer:
            customer_details.customer = blinkit_setting.default_customer
        if not customer_details.warehouse:
            customer_details.warehouse = blinkit_setting.default_warehouse
        return customer_details
    def make_sale_order(blinkit_po_data, order_details) -> str:
        order_items = order_details.get("item_data")
        purchase_order_details = order_details.get("purchase_order_details")
        transaction_date = getdate(purchase_order_details.get("issue_date"))
        customer_and_billing_details = get_customer_and_billing_details(order_details)
        so = frappe.new_doc("Sales Order")
        # so.blinkit_edi_order = 1
        # so.blinkit_po = blinkit_po_data
        so.customer = customer_and_billing_details.customer
        so.po_no = purchase_order_details.get("purchase_order_number")
        so.po_date = transaction_date
        so.delivery_date = getdate(purchase_order_details.get("po_expiry_date"))
        if customer_and_billing_details.billing_address:
            so.company_address = customer_and_billing_details.billing_address
        if customer_and_billing_details.customer_address:
            so.customer_address = customer_and_billing_details.customer_address
        if customer_and_billing_details.shipping_address:
            so.shipping_address_name = customer_and_billing_details.shipping_address
        so.transaction_date = transaction_date
        so.company = blinkit_setting.company
        so.set_warehouse = customer_and_billing_details.warehouse
        for item in order_items:
            item_details = {
                "item_code": get_item_code(item, customer_and_billing_details.customer),
                "customer_item_code": item.get("item_id"),
                "qty": item.get("units_ordered"),
                "uom": "Nos",
                "rate": item.get("cost_price"),
                "conversion_factor": 1.0,
                "warehouse": customer_and_billing_details.warehouse,
                "blinkit_po_line_number": item.get("line_number"),
                "blinkit_po": blinkit_po_data
            }
            so.append("items", item_details)
        so.taxes_and_charges = None
        so.set("taxes", [])
        so.run_method("set_missing_lead_customer_details")
        so.run_method("set_price_list_and_item_details")
        so.run_method("calculate_taxes_and_totals")
        so.payment_schedule = []
        so.flags.ignore_permissions = True
        so.insert()
        if blinkit_setting.submit_doc:
            so.submit()
        return so.name
    def make_quotation(blinkit_po_data, order_details) -> str:
        order_items = order_details.get("item_data")
        purchase_order_details = order_details.get("purchase_order_details")
        transaction_date = getdate(purchase_order_details.get("issue_date"))
        customer_and_billing_details = get_customer_and_billing_details(order_details)
        quotation = frappe.new_doc("Quotation")
        # quotation.blinkit_edi_order = 1
        # quotation.blinkit_po = blinkit_po_data
        quotation.quotation_to = "Customer"
        quotation.party_name = customer_and_billing_details.customer
        quotation.transaction_date = transaction_date
        quotation.valid_till = getdate(purchase_order_details.get("po_expiry_date"))
        quotation.company = blinkit_setting.company
        if customer_and_billing_details.billing_address:
            quotation.company_address = customer_and_billing_details.billing_address
        if customer_and_billing_details.customer_address:
            quotation.customer_address = customer_and_billing_details.customer_address
        if customer_and_billing_details.shipping_address:
            quotation.shipping_address_name = customer_and_billing_details.shipping_address
        for item in order_items:
            item_details = {
                "item_code": get_item_code(item, customer_and_billing_details.customer),
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
        quotation.flags.ignore_permissions = True
        quotation.insert()
        if blinkit_setting.submit_doc:
            quotation.submit()
        return quotation.name
    po_data = frappe.get_all("Blinkit PO Data", filters={"status":"Initiated"})
    for p in po_data:
        blinkit_po_data = frappe.get_doc("Blinkit PO Data", p.name)
        order_details = json.loads(blinkit_po_data.po_data)
        try:
            if blinkit_setting.sync_via == "Sales Order":
                sync_doc = make_sale_order(blinkit_po_data.name, order_details)
            elif blinkit_setting.sync_via == "Quotation":
                sync_doc = make_quotation(blinkit_po_data.name, order_details)
            blinkit_po_data.status = "Created"
            blinkit_po_data.sync_via = blinkit_setting.sync_via
            blinkit_po_data.sync_doc = sync_doc
            blinkit_po_data.save()
        except Exception:
            frappe.log_error("Error in creating Blinkit Sales Doc", reference_doctype="Blinkit PO Data", reference_name=p.name)
            continue

    return
