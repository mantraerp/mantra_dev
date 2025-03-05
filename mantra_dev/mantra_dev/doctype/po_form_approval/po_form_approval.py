# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class POFormApproval(Document):
	def validate(self):
		if frappe.db.exists("PO Form Approval", {'purchase_order':self.purchase_order, 'name': ['!=', self.name], 'docstatus': ['<', 2]}):
			frappe.throw(_("A PO Form Approval record already exists for Purchase Order {0}").format(self.purchase_order))


@frappe.whitelist()
def get_supplier_nda(supplier_id):
	# Fetch NDA File Link From Supplier Master
	return frappe.db.get_value("Supplier Attachments", {'parent': supplier_id, 'type_of_document': "NDA Signed ( In case Vendor is OEM / Tier-1 Distributor / Technical Services provider / IT servicer Provider)"}, 'attach_document')


@frappe.whitelist()
def get_purchase_order_against_details(purchase_order_id):
	# Fetch Purchase Order Details To Add and Append in PO Form Field Directly
	purchase_order_doc = frappe.get_doc("Purchase Order", purchase_order_id)
	item_code_list, request_list, material_request_list = [], [], []
	sales_person, bussiness_unit_name, bussiness_unit_email, sales_order = None, None, None, None

	for item in purchase_order_doc.items:
		item_code_list.append(item.item_code)
		if item.material_request:
			material_request_list.append(item.material_request)
			request_list.append(frappe.db.get_value("Material Request", item.material_request, 'owner'))
		if item.sales_order:
			sales_order = item.sales_order
	
	if sales_order:
		sales_person = frappe.db.get_value("Sales Order", sales_order, "custom_sales_person")
		if sales_person:
			top_sales_person = get_top_sales_person(sales_person)
			employee_id = frappe.db.get_value("Sales Person", top_sales_person, "employee")
			bussiness_unit_name = frappe.db.get_value("Employee", employee_id, 'employee_name')
			bussiness_unit_email = frappe.db.get_value("Employee", employee_id, 'user_id')

	return {
		'sales_order': sales_order,
		'material_request': ','.join(set(material_request_list)),
		'requester': ','.join(set(request_list)),
		'cost_center': purchase_order_doc.cost_center,
		'business_unit_name': bussiness_unit_name,
		'business_unit_email': bussiness_unit_email,
		'purpose': purchase_order_doc.custom_purpose,
		'approved_by': purchase_order_doc.custom_po_approver
	}



def get_top_sales_person(sales_person):
    # Find the top-level sales person by iterating upwards in the hierarchy.
    while sales_person:
        parent = frappe.db.get_value("Sales Person", sales_person, "parent_sales_person")        
        if not parent or parent == 'Sales Team':  
            return sales_person
        sales_person = parent