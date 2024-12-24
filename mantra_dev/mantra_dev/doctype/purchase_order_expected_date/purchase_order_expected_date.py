# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class PurchaseOrderExpectedDate(Document):
	pass
		

@frappe.whitelist()
def split_qty_method(docname, qty_to_split):
	doc = frappe.get_doc("Purchase Order Expected Date", docname)
	if flt(qty_to_split) <= 0 or flt(qty_to_split) > flt(doc.expected_qty):
		frappe.throw("Entered quantity exceeds the original expected quantity or is invalid.")
	doc.expected_qty -= flt(qty_to_split)
	doc.save()
	new_doc = frappe.new_doc("Purchase Order Expected Date")
	new_doc.purchase_order = doc.purchase_order
	new_doc.item_code = doc.item_code
	new_doc.expected_qty = qty_to_split
	new_doc.schedule_date = doc.schedule_date
	new_doc.expected_delivery_date = doc.expected_delivery_date
	new_doc.buffer_days=doc.buffer_days
	new_doc.qty=doc.qty
	new_doc.status = 'Approved'
	new_doc.final_expected_receive_date = doc.final_expected_receive_date
	new_doc.insert(ignore_permissions=True)
	return True