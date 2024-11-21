# Copyright (c) 2024, pwctech technologies private limited and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.data import get_url
from frappe.model.document import Document
from frappe.core.doctype.user.user import generate_keys
from frappe.utils.password import get_decrypted_password


class BlinkitSetting(Document):
	def validate(self):
		self.validate_user()
		if not self.url:
			self.url = get_url("/api/method/blinkit_connector/sync_order")
	
	def validate_user(self):
		if not frappe.db.get_value("User", {"name": self.blinkit_user}, "api_secret"):
			generate_keys(self.blinkit_user)

	@frappe.whitelist()
	def get_token(self):
		api_key = frappe.db.get_value("User", {"name": self.blinkit_user}, "api_key")
		api_secret = get_decrypted_password("User", self.blinkit_user, fieldname="api_secret")
		token =  "token {0}:{1}".format(api_key, api_secret)
		return frappe.msgprint("Auth Header: {0}".format(token))
