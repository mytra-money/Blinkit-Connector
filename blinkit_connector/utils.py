import frappe

class utils:
    def __init__(self, data):
        self.data = frappe._dict(data)
    
    def sync_order(self):
        blinkit_po_data = frappe.new_doc("Blinkit PO Data")
        blinkit_po_data.po_data = frappe.as_json(self.data, indent=4)
        blinkit_po_data.insert(ignore_permissions=True)
        return "success"