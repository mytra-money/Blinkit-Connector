import frappe

class utils:
    def __init__(self, data):
        self.data = frappe._dict(data)
    
    def sync_order(self):
        return "success"