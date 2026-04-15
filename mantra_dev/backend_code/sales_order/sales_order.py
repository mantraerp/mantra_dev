import json
from typing import Literal

import frappe
import frappe.utils
from frappe import _, qb
from frappe.contacts.doctype.address.address import get_company_address
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.query_builder.functions import Sum
from frappe.utils import add_days, cint, cstr, flt, get_link_to_form, getdate, nowdate, strip_html

from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
	unlink_inter_company_doc,
	update_linked_doc,
	validate_inter_company_party,
)
from erpnext.accounts.party import get_party_account
from erpnext.controllers.selling_controller import SellingController
from erpnext.manufacturing.doctype.blanket_order.blanket_order import (
	validate_against_blanket_order,
)
from erpnext.manufacturing.doctype.production_plan.production_plan import (
	get_items_for_material_requests,
)
from erpnext.selling.doctype.customer.customer import check_credit_limit
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
	get_sre_reserved_qty_details_for_voucher,
	has_reserved_stock,
)
from erpnext.stock.get_item_details import get_default_bom, get_price_list_rate
from erpnext.stock.stock_balance import get_reserved_qty, update_bin_qty

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}

@frappe.whitelist()
def make_raw_material_request(items, company, sales_order, project=None):
	if not frappe.has_permission("Sales Order", "write"):
		frappe.throw(("Not permitted"), frappe.PermissionError)

	if isinstance(items, str):
		items = frappe._dict(json.loads(items))

	for item in items.get("items"):
		item["include_exploded_items"] = items.get("include_exploded_items")
		item["ignore_existing_ordered_qty"] = items.get("ignore_existing_ordered_qty")
		item["include_raw_materials_from_sales_order"] = items.get("include_raw_materials_from_sales_order")

	items.update({"company": company, "sales_order": sales_order})

	customer_raw_materials=[]
	raw_materials = get_items_for_material_requests(items)
	if not raw_materials:
		frappe.msgprint(("Material Request not created, as quantity for Raw Materials already available."))
		return
	for i in raw_materials:
		doc = frappe.get_doc('Item', i['item_code'])

		if doc.is_customer_provided_item == 1:
			i['customer']=doc.customer
			customer_raw_materials.append(i)
   

	for i in customer_raw_materials:
		if i in raw_materials:
			raw_materials.remove(i)
   
			
	if customer_raw_materials:
		material_request = frappe.new_doc("Material Request")
		material_request.update(
			dict(
				doctype="Material Request",
				transaction_date=nowdate(),
				company=company,
				material_request_type="Customer Provided",
				customer=customer_raw_materials[0]['customer'],
			)
		)
		for item in customer_raw_materials:
			item_doc = frappe.get_cached_doc("Item", item.get("item_code"))

			schedule_date = add_days(nowdate(), frappe.cint(item_doc.lead_time_days))
			row = material_request.append(
				"items",
				{
					"item_code": item.get("item_code"),
					"qty": item.get("quantity"),
					"schedule_date": schedule_date,
					"warehouse": item.get("warehouse"),
					"sales_order": sales_order,
					"project": project,
					"custom_item_description": item.get("item_name"),
     
				},
			)

			if not (strip_html(item.get("description")) and strip_html(item_doc.description)):
				row.description = item_doc.item_name or item.get("item_code")

		material_request.insert()
		material_request.flags.ignore_permissions = 1
		material_request.run_method("set_missing_values")
		material_request.submit()
		cus_material_request = material_request
		# return material_request

	if raw_materials:
		material_request = frappe.new_doc("Material Request")
		material_request.update(
			dict(
				doctype="Material Request",
				transaction_date=nowdate(),
				company=company,
				material_request_type="Purchase",
			)
		)
		for item in raw_materials:
			item_doc = frappe.get_cached_doc("Item", item.get("item_code"))

			schedule_date = add_days(nowdate(), frappe.cint(item_doc.lead_time_days))
			row = material_request.append(
				"items",
				{
					"item_code": item.get("item_code"),
					"qty": item.get("quantity"),
					"schedule_date": schedule_date,
					"warehouse": item.get("warehouse"),
					"sales_order": sales_order,
					"project": project,
					"custom_item_description": item.get("item_name"),
				},
			)

			if not (strip_html(item.get("description")) and strip_html(item_doc.description)):
				row.description = item_doc.item_name or item.get("item_code")

		material_request.insert()
		material_request.flags.ignore_permissions = 1
		material_request.run_method("set_missing_values")
		material_request.submit()
        
	if customer_raw_materials:
		return material_request, cus_material_request
	else:
		return material_request
     