# Copyright (c) 2024, pwctech technologies private limited and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.data import get_url
from frappe.model.document import Document


class BlinkitSetting(Document):
	def validate(self):
		self.validate_user()
		if not self.url:
			self.url = get_url("/api/method/blinkit_connector/sync_order")
	
	def validate_user(self):
		return

	@frappe.whitelist()
	def get_token(self):
		token =  "token 19e349c2b8f069a:8873bdc356e3a1c"
		return frappe.msgprint("Auth Header: {0}".format(token))
