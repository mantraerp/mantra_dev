from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder # type: ignore
import frappe # type: ignore
from frappe.utils import  get_link_to_form # type: ignore
from frappe import _ # type: ignore
import json
from frappe.model.mapper import get_mapped_doc # type: ignore
from frappe.utils import flt # type: ignore
from erpnext.controllers.buying_controller import BuyingController # type: ignore
from erpnext.stock.stock_balance import get_ordered_qty, update_bin_qty # type: ignore
from erpnext.stock.utils import get_bin # type: ignore
from erpnext.accounts.doctype.sales_invoice.sales_invoice import update_linked_doc # type: ignore

class CustomPurchaseOrder(BuyingController):
	def on_submit(self):
		super().on_submit()

		if self.is_against_so():
			self.update_status_updater()

		self.update_prevdoc_status()
		if not self.is_subcontracted or self.is_old_subcontracting_flow:
			self.update_requested_qty()

		self.update_ordered_qty()
		self.validate_budget()
		self.update_reserved_qty_for_subcontract()

		frappe.get_doc("Authorization Control").validate_approving_authority(
			self.doctype, self.company, self.base_grand_total
		)

		self.update_blanket_order()

		update_linked_doc(self.doctype, self.name, self.inter_company_order_reference)

		self.auto_create_subcontracting_order()
		# self.bom_stock_validation()

	def is_against_so(self):
		return any(d.sales_order for d in self.items if d.sales_order)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.status_updater = [
			{
				"source_dt": "Purchase Order Item",
				"target_dt": "Material Request Item",
				"join_field": "material_request_item",
				"target_field": "ordered_qty",
				"target_parent_dt": "Material Request",
				"target_parent_field": "per_ordered",
				"target_ref_field": "stock_qty",
				"source_field": "stock_qty",
				"percent_join_field": "material_request",
			}
		]

	def update_status_updater(self):
		self.status_updater.append(
			{
				"source_dt": "Purchase Order Item",
				"target_dt": "Sales Order Item",
				"target_field": "ordered_qty",
				"target_parent_dt": "Sales Order",
				"target_parent_field": "",
				"join_field": "sales_order_item",
				"target_ref_field": "stock_qty",
				"source_field": "stock_qty",
			}
		)
		self.status_updater.append(
			{
				"source_dt": "Purchase Order Item",
				"target_dt": "Packed Item",
				"target_field": "ordered_qty",
				"target_parent_dt": "Sales Order",
				"target_parent_field": "",
				"join_field": "sales_order_packed_item",
				"target_ref_field": "qty",
				"source_field": "stock_qty",
			}
		)

	def update_ordered_qty(self, po_item_rows=None):
		"""update requested qty (before ordered_qty is updated)"""
		item_wh_list = []
		for d in self.get("items"):
			if (
				(not po_item_rows or d.name in po_item_rows)
				and [d.item_code, d.warehouse] not in item_wh_list
				and frappe.get_cached_value("Item", d.item_code, "is_stock_item")
				and d.warehouse
				and not d.delivered_by_supplier
			):
				item_wh_list.append([d.item_code, d.warehouse])
		for item_code, warehouse in item_wh_list:
			update_bin_qty(item_code, warehouse, {"ordered_qty": get_ordered_qty(item_code, warehouse)})

	def update_reserved_qty_for_subcontracting(self):
		for item in self.supplied_items:
			if item.rm_item_code:
				stock_bin = get_bin(item.rm_item_code, item.reserve_warehouse)
				stock_bin.update_reserved_qty_for_sub_contracting()

	def update_reserved_qty_for_subcontract(self):
		if self.is_old_subcontracting_flow:
			for d in self.supplied_items:
				if d.rm_item_code:
					stock_bin = get_bin(d.rm_item_code, d.reserve_warehouse)
					stock_bin.update_reserved_qty_for_sub_contracting(subcontract_doctype="Purchase Order")
	
	def auto_create_subcontracting_order(self):
		if self.is_subcontracted and not self.is_old_subcontracting_flow and self.custom_purchase_type == "Service Order":
			if frappe.db.get_single_value("Buying Settings", "auto_create_subcontracting_order"):
				override_make_subcontracting_order(self.name, save=True, submit=True, notify=True)

	def before_insert(self):
		if self.project:
			project = frappe.get_doc("Project",self.project)
			if project.custom_purchase_person:
				self.custom_purchase_person = project.custom_purchase_person
				

@frappe.whitelist()
def override_make_subcontracting_order(source_name, target_doc=None, save=False, submit=False, notify=False):
	target_doc = override_get_mapped_subcontracting_order(source_name, target_doc)

	if (save or submit) and frappe.has_permission(target_doc.doctype, "create"):
		target_doc.save()

		if submit and frappe.has_permission(target_doc.doctype, "submit", target_doc):
			try:
				target_doc.submit()
			except Exception as e:
				target_doc.add_comment("Comment", _("Submit Action Failed") + "<br><br>" + str(e))

		if notify:
			frappe.msgprint(
				_("Subcontracting Order {0} created.").format(
					get_link_to_form(target_doc.doctype, target_doc.name)
				),
				indicator="green",
				alert=True,
			)

	return target_doc


def override_get_mapped_subcontracting_order(source_name, target_doc=None):
	def post_process(source_doc, target_doc):
		target_doc.populate_items_table()

		if target_doc.set_warehouse:
			for item in target_doc.items:
				item.warehouse = target_doc.set_warehouse
		else:
			if source_doc.set_warehouse:
				for item in target_doc.items:
					item.warehouse = source_doc.set_warehouse
			else:
				for idx, item in enumerate(target_doc.items):
					item.warehouse = source_doc.items[idx].warehouse

	if target_doc and isinstance(target_doc, str):
		target_doc = json.loads(target_doc)
		for key in ["service_items", "items", "supplied_items"]:
			if key in target_doc:
				del target_doc[key]
		target_doc = json.dumps(target_doc)

	target_doc = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Subcontracting Order",
				"field_map": {
                    "custom_set_reserve_warehouse": "set_reserve_warehouse",
                },
				"field_no_map": ["total_qty", "total", "net_total"],
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Purchase Order Item": {
				"doctype": "Subcontracting Order Service Item",
				"field_map": {
					"name": "purchase_order_item",
					"material_request": "material_request",
					"material_request_item": "material_request_item",
				},
				"field_no_map": [],
			},
		},
		target_doc,
		post_process,
	)
	return target_doc


@frappe.whitelist()
def is_subcontracting_order_created(po_name) -> bool:
	return (
		True
		if frappe.db.exists("Subcontracting Order", {"purchase_order": po_name, "docstatus": ["=", 1]})
		else False
	)
 

def set_missing_values(source, target):
	target.run_method("set_missing_values")
	target.run_method("calculate_taxes_and_totals")

@frappe.whitelist()
def override_make_purchase_receipt(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		target.qty = flt(obj.qty) - flt(obj.received_qty)
		target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.conversion_factor)
		target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
		target.base_amount = (
			(flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate) * flt(source_parent.conversion_rate)
		)

	doc = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Purchase Receipt",
				"field_map": {"supplier_warehouse": "supplier_warehouse"},
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Purchase Order Item": {
				"doctype": "Purchase Receipt Item",
				"field_map": {
					"name": "purchase_order_item",
					"parent": "purchase_order",
					"bom": "bom",
					"material_request": "material_request",
					"material_request_item": "material_request_item",
					"sales_order": "sales_order",
					"sales_order_item": "sales_order_item",
					"wip_composite_asset": "wip_composite_asset",
					"fg_item": "custom_fg_item"
				},
				"postprocess": update_item,
				"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty)
				and doc.delivered_by_supplier != 1,
			},
			"Purchase Taxes and Charges": {"doctype": "Purchase Taxes and Charges", "reset_value": True},
		},
		target_doc,
		set_missing_values,
	)

	return doc