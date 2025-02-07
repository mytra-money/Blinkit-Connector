# Copyright (c) 2024, pwctech technologies private limited and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.data import get_url
from frappe.model.document import Document
from frappe.core.doctype.user.user import generate_keys
from frappe.utils.password import get_decrypted_password
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields



class BlinkitSetting(Document):
	def validate(self):
		self.validate_user()
		if not self.url:
			self.url = get_url("/api/method/blinkit_connector/sync_order")
		setup_custom_fields()
	
	def validate_user(self):
		if not frappe.db.get_value("User", {"name": self.blinkit_user}, "api_secret"):
			generate_keys(self.blinkit_user)

	@frappe.whitelist()
	def get_token(self):
		api_key = frappe.db.get_value("User", {"name": self.blinkit_user}, "api_key")
		api_secret = get_decrypted_password("User", self.blinkit_user, fieldname="api_secret")
		token =  "token {0}:{1}".format(api_key, api_secret)
		return frappe.msgprint("Auth Header: {0}".format(token))


def setup_custom_fields():
	custom_fields = {
		"Quotation": [
			dict(
				fieldname="blinkit_edi_order",
				label="Blinkit EDI Order",
				fieldtype="Check",
				insert_after="title",
				read_only=1,
				print_hide=1,
			),
			dict(
				fieldname="blinkit_po",
				label="Blinkit PO Data",
				fieldtype="Link",
				insert_after="blinkit_edi_order",
				options="Blinkit PO Data",
				read_only=1,
				print_hide=1,
			)
		],
		"Sales Order": [
			dict(
				fieldname="blinkit_edi_order",
				label="Blinkit EDI Order",
				fieldtype="Check",
				insert_after="title",
				read_only=1,
				print_hide=1,
			),
			dict(
				fieldname="blinkit_po",
				label="Blinkit PO Data",
				fieldtype="Link",
				insert_after="blinkit_edi_order",
				options="Blinkit PO Data",
				read_only=1,
				print_hide=1,
			)
		],
		"Delivery Note": [
			dict(
				fieldname="blinkit_edi_order",
				label="Blinkit EDI Order",
				fieldtype="Check",
				insert_after="title",
				read_only=1,
				print_hide=1,
			),
			dict(
				fieldname="blinkit_po",
				label="Blinkit PO Data",
				fieldtype="Link",
				insert_after="blinkit_edi_order",
				options="Blinkit PO Data",
				read_only=1,
				print_hide=1,
			)
		],
		"Sales Invoice": [
			dict(
				fieldname="blinkit_edi_order",
				label="Blinkit EDI Order",
				fieldtype="Check",
				insert_after="title",
				read_only=1,
				print_hide=1,
			),
			dict(
				fieldname="blinkit_po",
				label="Blinkit PO Data",
				fieldtype="Link",
				insert_after="blinkit_edi_order",
				options="Blinkit PO Data",
				read_only=1,
				print_hide=1,
			)
		]
	}

	create_custom_fields(custom_fields)

