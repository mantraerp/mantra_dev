# import frappe
# from frappe.model.document import Document
# from frappe.model.mapper import get_mapped_doc
# import json

# @frappe.whitelist()
# def make_dc(doc, method=None):
#     custom_settings = frappe.get_single('Custom Settings')

#     if custom_settings.auto_create_delivery_note == 1:
#         print("Sales Invoice Name:", doc.name)
#         frappe.msgprint(str(len(doc.items)))
#         if len(doc.items) == 1:
#             for item in doc.items:
#                 if not item.get('item_code'):
#                     is_service_item = frappe.db.get_value("Item", item.get('item_code'), 'custom_is_service_item')
#                     if is_service_item == 0:
#                         dc = frappe.new_doc("Delivery Note")
#                         dc.custom_sales_invoice_no = doc.name
#                         dc.customer = doc.customer
#                         dc.posting_date = doc.posting_date
#                         dc.posting_time = doc.posting_time
#                         dc.custom_sales_person = doc.custom_sales_person
#                         dc.company = doc.company
#                         dc.set_warehouse = doc.set_warehouse
#                         dc.dispatch_address_name = ""
#                         dc.items = []
#                         print("Processing Item:", item)
#                         if not item.get('item_code'):
#                             frappe.throw("Item code is missing in one of the items.")
#                         else:
#                                 dn_item = dc.append('items', {})
#                                 dn_item.item_code = item.item_code
#                                 dn_item.item_name = item.item_name
#                                 dn_item.qty = item.qty
#                                 dn_item.uom = item.uom
#                                 dn_item.rate = item.rate
#                                 dn_item.amount = item.amount
#                                 dn_item.against_sales_invoice = doc.name
#                                 dn_item.si_detail = item.name
#                                 if item.get('sales_order'):
#                                     dn_item.against_sales_order = item.sales_order
#                                     dn_item.so_detail = item.so_detail
#                         dc.total = doc.total if doc.total is not None else 0
#                         dc.net_total = doc.net_total if doc.net_total is not None else 0
#                         dc.grand_total = doc.grand_total if doc.grand_total is not None else 0
#                         dc.base_total = doc.base_total if doc.base_total is not None else 0
#                         dc.base_net_total = doc.base_net_total if doc.base_net_total is not None else 0
#                         dc.base_grand_total = doc.base_grand_total if doc.base_grand_total is not None else 0
#                         dc.insert(ignore_permissions=True)
#                         frappe.db.commit()
#                         for dc_items in dc.items:
#                             if dc_items.so_detail:
#                                 qty = frappe.db.get_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty")
#                                 print(qty)
#                                 if qty is None:
#                                     qty = 0
#                                 t_qty = qty + dc_items.qty
#                                 frappe.db.set_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty", t_qty)
#                         frappe.db.commit()
#                         frappe.msgprint(f"Delivery Note {dc.name} created successfully.")
#         else:
#             dc = frappe.new_doc("Delivery Note")
#             dc.custom_sales_invoice_no = doc.name
#             dc.customer = doc.customer
#             dc.posting_date = doc.posting_date
#             dc.posting_time = doc.posting_time
#             dc.custom_sales_person = doc.custom_sales_person
#             dc.company = doc.company
#             dc.set_warehouse = doc.set_warehouse
#             dc.dispatch_address_name = ""
#             dc.items = []
#             for item in doc.items:
#                 print("Processing Item:", item)
#                 if not item.get('item_code'):
#                     frappe.throw("Item code is missing in one of the items.")
#                 else:
#                     is_service_item = frappe.db.get_value("Item", item.get('item_code'), 'custom_is_service_item')
#                     if is_service_item == 0:
#                         dn_item = dc.append('items', {})
#                         dn_item.item_code = item.item_code
#                         dn_item.item_name = item.item_name
#                         dn_item.qty = item.qty
#                         dn_item.uom = item.uom
#                         dn_item.rate = item.rate
#                         dn_item.amount = item.amount
#                         dn_item.against_sales_invoice = doc.name
#                         dn_item.si_detail = item.name
#                         if item.get('sales_order'):
#                             dn_item.against_sales_order = item.sales_order
#                             dn_item.so_detail = item.so_detail
#             dc.total = doc.total if doc.total is not None else 0
#             dc.net_total = doc.net_total if doc.net_total is not None else 0
#             dc.grand_total = doc.grand_total if doc.grand_total is not None else 0
#             dc.base_total = doc.base_total if doc.base_total is not None else 0
#             dc.base_net_total = doc.base_net_total if doc.base_net_total is not None else 0
#             dc.base_grand_total = doc.base_grand_total if doc.base_grand_total is not None else 0

        
#             dc.insert(ignore_permissions=True)
#             frappe.db.commit()
#             for dc_items in dc.items:
#                 if dc_items.so_detail:
#                     qty = frappe.db.get_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty")
#                     print(qty)
#                     if qty is None:
#                         qty = 0
#                     t_qty = qty + dc_items.qty
#                     frappe.db.set_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty", t_qty)
#             frappe.db.commit()
#             frappe.msgprint(f"Delivery Note {dc.name} created successfully.")
       


import frappe
from frappe import _, msgprint, throw
from frappe.contacts.doctype.address.address import get_address_display
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import add_days, cint, cstr, flt, formatdate, get_link_to_form, getdate, nowdate

import erpnext
from erpnext.accounts.deferred_revenue import validate_service_stop_date
from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
	get_loyalty_program_details_with_points,
	validate_loyalty_points,
)
from erpnext.accounts.doctype.repost_accounting_ledger.repost_accounting_ledger import (
	validate_docs_for_deferred_accounting,
	validate_docs_for_voucher_types,
)
from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
	get_party_tax_withholding_details,
)
from erpnext.accounts.general_ledger import get_round_off_account_and_cost_center
from erpnext.accounts.party import get_due_date, get_party_account, get_party_details
from erpnext.accounts.utils import cancel_exchange_gain_loss_journal, get_account_currency
from erpnext.assets.doctype.asset.depreciation import (
	depreciate_asset,
	get_disposal_account_and_cost_center,
	get_gl_entries_on_asset_disposal,
	get_gl_entries_on_asset_regain,
	reset_depreciation_schedule,
	reverse_depreciation_entry_made_after_disposal,
)
from erpnext.assets.doctype.asset_activity.asset_activity import add_asset_activity
from erpnext.controllers.accounts_controller import validate_account_head
from erpnext.controllers.selling_controller import SellingController
from erpnext.projects.doctype.timesheet.timesheet import get_projectwise_timesheet_data
from erpnext.setup.doctype.company.company import update_company_current_month_sales
from erpnext.stock.doctype.delivery_note.delivery_note import update_billed_amount_based_on_so
from erpnext.stock.doctype.serial_no.serial_no import get_delivery_note_serial_no, get_serial_nos

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}







@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty = flt(source_doc.qty) - flt(source_doc.delivered_qty)
		target_doc.stock_qty = target_doc.qty * flt(source_doc.conversion_factor)

		target_doc.base_amount = target_doc.qty * flt(source_doc.base_rate)
		target_doc.amount = target_doc.qty * flt(source_doc.rate)

	doclist = get_mapped_doc(
		"Sales Invoice",
		source_name,
		{
			"Sales Invoice": {"doctype": "Delivery Note", "validation": {"docstatus": ["=", 1]}},
			"Sales Invoice Item": {
				"doctype": "Delivery Note Item",
				"field_map": {
					"name": "si_detail",
					"parent": "against_sales_invoice",
					"serial_no": "serial_no",
					"sales_order": "against_sales_order",
					"so_detail": "so_detail",
					"cost_center": "cost_center",
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.delivered_by_supplier != 1 and doc.custom_is_service_item != 1,
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "reset_value": True},
			"Sales Team": {
				"doctype": "Sales Team",
				"field_map": {"incentives": "incentives"},
				"add_if_empty": True,
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist


