from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder # type: ignore
import frappe # type: ignore
from frappe.utils import  get_link_to_form # type: ignore
from frappe import _ # type: ignore
import json
from frappe.model.mapper import get_mapped_doc # type: ignore
from frappe.utils import flt # type: ignore

class CustomPurchaseOrder(PurchaseOrder):
	def on_submit(self):
		super().on_submit()
		if po_form := frappe.db.get_value("PO Form Approval", {"purchase_order": self.name, "docstatus": 0}, "name"):
			po_form_doc = frappe.get_doc("PO Form Approval", po_form)
			po_form_doc.submit()

	def auto_create_subcontracting_order(self):
		if self.is_subcontracted and not self.is_old_subcontracting_flow and self.custom_purchase_type == "Service Order":
			if frappe.db.get_single_value("Buying Settings", "auto_create_subcontracting_order"):
				override_make_subcontracting_order(self.name, save=True, submit=True, notify=True)

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

@frappe.whitelist()
def get_purchase_person():
	cur_user = frappe.session.user
	if cur_user in ["Administrator", "Guest"]:
		return
	
	employee = frappe.get_value("Employee",{"user_id" : cur_user},'name')
	if not employee:
		return
	
	purchase_person = frappe.get_value("Purchase Person",{"employee":employee},'name')
	if not purchase_person:
		return
	
	return purchase_person