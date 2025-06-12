import frappe
import json
import requests
from frappe.integrations.utils import create_request_log
from frappe.utils.data import flt, format_date

class BlinkitRepository:
    def __init__(self):
        blinkit_settings = frappe.get_cached_doc("Blinkit Setting")
        if blinkit_settings.base_url:
            self.base_url = blinkit_settings.base_url
            self.auth_header = blinkit_settings.get_password("auth_header", raise_exception=False)
        else:
            frappe.throw("Please set the Base URL in Blinkit Setting")
    
    def make_request(
        self,
        method: str = "GET",
        append_to_base_uri: str = "",
        data: dict = None,
        log_request: bool =True
    ) -> dict:
        url = self.base_url + append_to_base_uri
        headers = {}
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Token {0}".format(self.auth_header)
        }
        if log_request:
            integration_request = create_request_log(data=data, service_name="BlinkIt EDI", request_headers=headers, is_remote_request=1, url=url)
        try:
            response = requests.request(
                method=method,
                url=url,
                data=json.dumps(data),
                headers=headers
            )
            response.raise_for_status()
            
            if log_request:
                integration_request.db_set("status", "Completed")
                integration_request.db_set("output", frappe.as_json(response.json()))
                frappe.db.commit()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if log_request:
                integration_request.db_set("status", "Failed")
                integration_request.db_set("error", f"HTTP Error {response.status_code}: {response.text}")
                frappe.db.commit()
                raise
        
        except Exception as e:
            if log_request:
                integration_request.db_set("status", "Failed")
                integration_request.db_set("error", str(e))
                frappe.db.commit()
                raise

    def acknowledge_po(self, blinkit_po):
        blinkit_po_data = frappe.get_cached_doc("Blinkit PO Data", blinkit_po)
        po_data = json.loads(blinkit_po_data.po_data)
        sales_doc = frappe.get_cached_doc(blinkit_po_data.sync_via, blinkit_po_data.sync_doc)
        item_errors = []
        data = {
                "RECEIVER_CODE": po_data.get("receiver_code"),
                "PO_NUMBER": int(blinkit_po_data.po_number),
                "STATUS": "Success",
                "EVENT_NAME": "PO_CREATION",
                "EVENT_MESSAGE": "PO_CREATION"
            }
        
        for po_item in po_data.get("item_data", []):
            matching_sales_item = next(
                (i for i in sales_doc.items if i.blinkit_po_line_number == po_item.get("line_number")),
                None
                )
            if matching_sales_item:
                po_qty = float(po_item.get("units_ordered", 0))
                sales_qty = float(matching_sales_item.qty)
                if sales_qty < po_qty:
                    item_errors.append({"item_id": po_item.get("item_id"), "error_message": "insufficient stock"})    
            else:
                item_errors.append({"item_id": po_item.get("item_id"), "error_message": "insufficient stock"})
        
        if not len(item_errors):
            data["STATUS"] = "Success"
        else:
            data["STATUS"] = "PARTIAL_SUCCESS"
            data["ITEM_ERRORS"] = item_errors
        url = "edi/edi-response-json/"
        try:
            self.make_request("POST", url, data)
        except Exception:
            frappe.log_error("BlinkIt Acknowledge PO Error")
            frappe.throw("Cannot Acknowledge BlinkIt PO")
    
    def send_asn(self, sales_invoice, blinkit_po, shipment):
        blinkit_po_data = frappe.get_cached_doc("Blinkit PO Data", blinkit_po)
        company_address = frappe.get_cached_doc("Address", sales_invoice.company_address)
        shipment_doc  = frappe.get_cached_doc("Shipment", shipment)
        po_data = json.loads(blinkit_po_data.po_data)
        po_items_by_line = {
            item["line_number"]: item for item in po_data.get("item_data", [])
        }
        data = {
            "PONumber": blinkit_po_data.po_number,
            "VendorInvoiceNumber": sales_invoice.name,
            "InvoiceDate": format_date(sales_invoice.posting_date, "yyyy-mm-dd"),
            "DeliveryDate": format_date(shipment_doc.pickup_date, "yyyy-mm-dd"),
            "TaxDistribution":[],
            "BasicPrice": sales_invoice.base_net_total,
            "LandingPrice": sales_invoice.base_grand_total,
            "Quantity": sales_invoice.total_qty,
            "ItemCount": len(set(row.item_code for row in sales_invoice.items)),
            "POStatus": "PO_PENDING", # to be calculated PO_FULFILLED/PO_PENDING
            "SupplierDetails": {
                "Supplier": sales_invoice.company,
                "GSTIN": sales_invoice.company_gstin,
                "SupplierAddress": {
                    "addressLine1": company_address.address_line1,
                    "addressLine2": company_address.address_line2,
                    "city": company_address.city,
                    "country": company_address.country,
                    "pincode": company_address.pincode,
                    "state": company_address.state
                }
            },
            "BuyerDetails":{
                "GSTIN": po_data.get("financial_details").get("gst_tin")
            },
            "ShipmentDetails": {
                "EWayBillNumber": "",
                "DeliveryType": "COURIER",
                "DeliveryPartner": "Test Transporter", #shipment_doc.transporter,
                "DeliveryPartnerID": "TEST",#shipment_doc.gst_transporter_id,
                "DeliveryTrackingCode": "TEST123",#shipment_doc.awb_number
            },
            "items": []
        }
        for item in sales_invoice.items:
            # data["TotalInvoiceCGST"]+=item.cgst_amount
            # data["TotalInvoiceSGST"]+=item.sgst_amount
            # data["TotalInvoiceIGST"]+=item.igst_amount
            # data["TotalInvoiceCESS"]+=item.cess_amount
            # data["Total_Invoice_ADV_CESS"]+=item.cess_non_advol_amount
            po_item = po_items_by_line.get(item.blinkit_po_line_number, {})
            item_data = {
                "ItemID": po_item.get("item_id"),
                "SKUDescription": po_item.get("name"),
                "BatchNumber": "",
                "UPC": po_item.get("upc"),
                "MRP": po_item.get("mrp"),
                "Quantity": item.qty,
                "HSNCode": item.gst_hsn_code,
                "TaxDistribution": {
                    "CGSTPercentage": item.cgst_rate,
                    "SGSTPercentage": item.sgst_rate,
                    "IGSTPercentage": item.igst_rate,
                    "UGSTPercentage": 0.0,
                    "CESSPercentage": item.cess_rate,
                    "AdditionalCESSValue": item.cess_non_advol_rate,
                },
                "UnitBasicPrice": item.base_rate,
                "UnitLandingPrice": flt(item.base_rate+item.cgst_amount/item.qty+item.sgst_amount/item.qty+item.igst_amount/item.qty+item.cess_amount/item.qty+item.cess_non_advol_amount/item.qty, precision=2),
                # "ExpiryDate": "",
                # "MfgDate": "",
                "Grammage": "",
                "UOM": item.uom,
                }
            
            data["items"].append(item_data)

        url = "edi/v3/asn-response/{0}/".format(blinkit_po_data.po_number)
        try:
            asn_ackn = self.make_request("POST", url, data)
            if int(asn_ackn["status"]) == 1:
                frappe.msgprint("ASN Submitted Sucessfuly for Sales Invoice: {0}".format(sales_invoice.name))
        except Exception:
            frappe.log_error("BlinkIt ASN Error")
            frappe.throw("Cannot send ASN for BlinkIt PO")


@frappe.whitelist()
def submit_asn(shipment):
    shipment_doc  = frappe.get_cached_doc("Shipment", shipment)
    delivery_notes = list(set(row.delivery_note for row in shipment_doc.shipment_delivery_note))
    delivery_note_si_rows = frappe.get_all(
        "Delivery Note Item",
        fields=["against_sales_invoice"],
        filters=[["parent", "in", delivery_notes]]
    )
    delivery_note_sales_invoices = {row.against_sales_invoice for row in delivery_note_si_rows if row.against_sales_invoice}
    sales_invoice_items = frappe.get_all(
        "Sales Invoice Item",
        fields=["parent"],
        filters=[
            ["delivery_note", "in", delivery_notes],
            ["docstatus", "=", 1]
        ]
    )
    sales_invoices_delivery_note = {row.parent for row in sales_invoice_items if row.parent}
    sales_invoices = delivery_note_sales_invoices.union(sales_invoices_delivery_note)
    for s in sales_invoices:
        sales_invoice = frappe.get_cached_doc("Sales Invoice", s)
        blinkit_po = sales_invoice.items[0].blinkit_po
        if blinkit_po:
            BlinkitRepository().send_asn(sales_invoice, blinkit_po, shipment_doc)
            return "Success"
        else:
            frappe.msgprint("Sales Invoice {} is not synced via BlinkIt".format(s))