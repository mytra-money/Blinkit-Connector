import frappe
import json
import requests
from frappe.integrations.utils import create_request_log

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
            "Accept": "application/json",
            "Authorization": "Token {0}".format(self.auth_header)
        }
        headers["Accept"] = "application/json"
        if log_request:
            integration_request = create_request_log(data=data, service_name="BlinkIt EDI", request_headers=headers, is_remote_request=1, url=url)
        try:
            response = requests.request(
                method=method,
                url=url,
                data=frappe.as_json(data, indent=1) if isinstance(data, dict) else data,
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
        data = {
                "RECEIVER_CODE": po_data.get("receiver_code"),
                "PO_NUMBER": int(blinkit_po_data.po_number),
                "STATUS": "Success",
                "EVENT_NAME": "PO_CREATION",
                "EVENT_MESSAGE": "PO_CREATION"
            }
        url = "edi/edi-response/"
        try:
            self.make_request("POST", url, data)
        except Exception:
            frappe.log_error("BlinkIt Acknowledge PO Error")
            frappe.throw("Cannot Acknowledge BlinkIt PO")
    
    def send_asn(self, sales_invoice):
        sales_invoice = frappe.get_cached_doc("Sales Invoice", sales_invoice)
        blinkit_po_data = frappe.get_cached_doc("Blinkit PO Data", sales_invoice.blinkit_po)
        po_data = json.loads(blinkit_po_data.po_data)
        data = {
            "PONumber": blinkit_po_data.po_number,
            "VendorInvoiceNumber": sales_invoice.name,
            "InvoiceDate": "25/04/2024",
            "DeliveryDate": "18/04/2024",
            "TotalInvoiceCGST": "1816.92",
            "TotalInvoiceSGST": "1816.92",
            "TotalInvoiceUGST": "0",
            "TotalInvoiceIGST": "0",
            "TotalInvoiceCESS": "0",
            "Total_Invoice_ADV_CESS": "0",
            "TotalTaxAmount": "3633.84",
            "TotalBasicPrice": "20188",
            "TotalLandingCost": "23820",
            "BillToGST": "27AADCH7038R1ZX",
            "POStatus": "PO_FULFILLED",
            "items": [
                {
                "ItemID": "10016623",
                "SKUDescription": "SKU Description",
                "UPC": "8901023019258",
                "Quantity": "50.000",
                "MRP": "410.00",
                "HSNCode": "38089199",
                "CGST_Percentage": "9.0",
                "SGST_Percentage": "9.0",
                "IGST_Percentage": "18.0",
                "UGST_Percentage": "0",
                "CESS_Percentage": "0",
                "AdditionalCESS_Percentage": "0",
                "BasicPrice": "260",
                "LandedCost": "310",
                "Grammage": "",
                "WeightUOM": "",
                }
            ]
        }
        return