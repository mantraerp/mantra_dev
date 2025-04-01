# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from mantra_dev.backend_code.purchase_order.purchase_order import get_stock_details


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
	item_code_list, request_list, material_request_list, stock_details_list,approver_list = [], [], [], [], []
	sales_person, bussiness_unit_name, bussiness_unit_email, sales_order = None, None, None, None

	for item in purchase_order_doc.items:
		item_code_list.append(item.item_code)
		if item.material_request:
			material_request_list.append(item.material_request)
			approver_list.append(frappe.db.get_value("Comment", {"comment_type": "Workflow", "reference_doctype": "Material Request", "reference_name": item.material_request, "content": "Approved"}, "comment_email"))
			request_list.append(frappe.db.get_value("Material Request", item.material_request, 'owner'))
		if item.sales_order:
			sales_order = item.sales_order
		
		stock_details = get_stock_details(item.item_code, item.warehouse or None)
		demand = 0
		if item.material_request:
			demand += frappe.db.get_value("Material Request Item", {'parent': item.material_request, 'docstatus': ['<', 2], 'item_code': item.item_code}, 'qty')
		stock_details_list.append({
			"item_code": item.item_code,
			"item_name": item.item_name,
			"qty": item.qty,
			"target_warehouse_qty": stock_details['available_qty_in_target'],
			"current_stock": stock_details['total_available_stock'],
			"demand": 0
		})

	price_comparison = [{
		'supplier_name': purchase_order_doc.supplier_name,
		'payment_terms': frappe.db.get_value("Supplier", purchase_order_doc.supplier, "payment_terms") or ''
	}]

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
		'approved_by': ','.join(set(approver_list)),
		'price_comparison': price_comparison,
		'stock_detail': stock_details_list
	}



def get_top_sales_person(sales_person):
    # Find the top-level sales person by iterating upwards in the hierarchy.
    while sales_person:
        parent = frappe.db.get_value("Sales Person", sales_person, "parent_sales_person")        
        if not parent or parent == 'Sales Team':  
            return sales_person
        sales_person = parent