import frappe
from frappe.utils import get_datetime_str
import datetime
import pytz

class utils:
    def __init__(self, data):
        self.data = frappe._dict(data)
    
    def sync_order(self):
        data = self.data
        po_number = data.get("purchase_order_details").get("purchase_order_number")
        if data.get("event_name") == "PO_CREATION":
            blinkit_po_data = frappe.new_doc("Blinkit PO Data")
            blinkit_po_data.po_number = po_number
            blinkit_po_data.po_data = frappe.as_json(data, indent=4)
            blinkit_po_data.insert(ignore_permissions=True)
            response = {
                "success": True,
                "message": "Processing PO",
                "timestamp": get_datetime_str(datetime.datetime.now(pytz.UTC)),
                "data": {
                    "po_status": "processing",
                    "po_number": po_number,
                }
            }
            return response
        else:
            frappe.log_error("Incorrect Blinkit request")
            frappe.local.response['http_status_code'] = 417
            frappe.throw("Incorrect Blinkit Request")