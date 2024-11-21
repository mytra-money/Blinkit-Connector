import frappe
from blinkit_connector.utils import utils

@frappe.whitelist()
def blinkit_connector():
    url_parts = frappe.request.path[1:].split("/",3)
    request = url_parts[-1] if url_parts[-1][0] != "/" else url_parts[-1][1:]
    data = frappe._dict(frappe.local.form_dict)
    data.pop("cmd")
    try: 
        services = utils(data)
        if hasattr(services, request):
            return getattr(services, request)()
        else:
            frappe.throw("Invalid Request")
    except Exception as e:
        raise frappe.ValidationError(e)
