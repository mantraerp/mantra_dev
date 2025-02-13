import frappe
from frappe import _, throw
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder.functions import CombineDatetime
from frappe.utils import cint, flt, get_datetime, getdate, nowdate
from pypika import functions as fn

import erpnext
from erpnext.accounts.utils import get_account_currency
from erpnext.assets.doctype.asset.asset import get_asset_account, is_cwip_accounting_enabled
from erpnext.buying.utils import check_on_hold_or_closed_status
from erpnext.controllers.accounts_controller import merge_taxes
from erpnext.controllers.buying_controller import BuyingController
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt
from erpnext.stock.doctype.delivery_note.delivery_note import make_inter_company_transaction
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import update_billed_amount_based_on_po
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import update_billing_percentage
from erpnext.buying.doctype.purchase_order.purchase_order import set_missing_values
from frappe.utils import  get_link_to_form
import json

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}

class CustomPurchaseReceipt(PurchaseReceipt):
	def on_submit(self):
		super().on_submit()

		# Check for Approving Authority
		frappe.get_doc("Authorization Control").validate_approving_authority(
			self.doctype, self.company, self.base_grand_total
		)

		self.update_prevdoc_status()
		if flt(self.per_billed) < 100:
			self.update_billing_status()
		else:
			self.db_set("status", "Completed")

		self.make_bundle_for_sales_purchase_return()
		self.make_bundle_using_old_serial_batch_fields()
		# Updating stock ledger should always be called after updating prevdoc status,
		# because updating ordered qty, reserved_qty_for_subcontract in bin
		# depends upon updated ordered qty in PO
		self.update_stock_ledger()
		self.make_gl_entries()
		self.repost_future_sle_and_gle()
		self.set_consumed_qty_in_subcontract_order()
		self.reserve_stock_for_sales_order()
		if self.is_subcontracted:
			self.bom_stock_validation()
	
	def update_billing_status(self, update_modified=True):
		updated_pr = [self.name]
		po_details = []
		for d in self.get("items"):
			if d.get("purchase_invoice") and d.get("purchase_invoice_item"):
				d.db_set("billed_amt", d.amount, update_modified=update_modified)
			elif d.purchase_order_item:
				po_details.append(d.purchase_order_item)

		if po_details:
			updated_pr += update_billed_amount_based_on_po(po_details, update_modified, self)

		for pr in set(updated_pr):
			pr_doc = self if (pr == self.name) else frappe.get_doc("Purchase Receipt", pr)
			update_billing_percentage(pr_doc, update_modified=update_modified)
	
	def reserve_stock_for_sales_order(self):
		if (
			self.is_return
			or not frappe.db.get_single_value("Stock Settings", "enable_stock_reservation")
			or not frappe.db.get_single_value(
				"Stock Settings", "auto_reserve_stock_for_sales_order_on_purchase"
			)
		):
			return

		self.reload()  # reload to get the Serial and Batch Bundle Details

		so_items_details_map = {}
		for item in self.items:
			if item.sales_order and item.sales_order_item:
				item_details = {
					"sales_order_item": item.sales_order_item,
					"item_code": item.item_code,
					"warehouse": item.warehouse,
					"qty_to_reserve": item.stock_qty,
					"from_voucher_no": item.parent,
					"from_voucher_detail_no": item.name,
					"serial_and_batch_bundle": item.serial_and_batch_bundle,
				}
				so_items_details_map.setdefault(item.sales_order, []).append(item_details)

		if so_items_details_map:
			if get_datetime(f"{self.posting_date} {self.posting_time}") > get_datetime():
				return frappe.msgprint(
					_("Cannot create Stock Reservation Entries for future dated Purchase Receipts.")
				)

			for so, items_details in so_items_details_map.items():
				so_doc = frappe.get_doc("Sales Order", so)
				so_doc.create_stock_reservation_entries(
					items_details=items_details,
					from_voucher_type="Purchase Receipt",
					notify=True,
				)
	
	def enable_recalculate_rate_in_sles(self):
		sle_table = frappe.qb.DocType("Stock Ledger Entry")
		(
			frappe.qb.update(sle_table)
			.set(sle_table.recalculate_rate, 1)
			.where(sle_table.voucher_no == self.name)
			.where(sle_table.voucher_type == "Purchase Receipt")
		).run()

	def bom_stock_validation(self):
		"""
		Validation check the bom raw matrial is available or not in the stock
		If raw matrial is available in the stock so create the auto stock entry for 
		Matrial Transfer and Subcontracting order 
		"""
		items, all_stock_available = self.check_raw_matrial_stock()
		if items and all_stock_available:
			self.auto_create_stock_entry(items)
			self.auto_create_subcontracting_receipt()
			
		elif items is not None:
			msg = ""
			for item in items:
				shortage_qty = item['required_qty'] - item['available_stock']
				if shortage_qty > 0:
					msg += (f"<b>Service Item:</b> {item['service_item']}<br>"
							f"<b>Finished Good Item:</b> {item['finished_item']}<br>"
							f"<b>Raw Material:</b> {item['raw_material']}<br>"
							f"<b>Required Qty:</b> {item['required_qty']}<br>"
							f"<b>Available Qty:</b> {item['available_stock']}<br>"
							f"<b>Shortage Qty:</b> {item['required_qty'] - item['available_stock']}<br><br>")
			if msg:
				frappe.throw(msg)
		
		elif not all_stock_available:
			msg = ""
			for item in items:
				shortage_qty = item['required_qty'] - item['available_stock']
				if shortage_qty > 0:
					msg += (f"<b>Service Item:</b> {item['service_item']}<br>"
							f"<b>Finished Good Item:</b> {item['finished_item']}<br>"
							f"<b>Raw Material:</b> {item['raw_material']}<br>"
							f"<b>Required Qty:</b> {item['required_qty']}<br>"
							f"<b>Available Qty:</b> {item['available_stock']}<br>"
							f"<b>Shortage Qty:</b> {item['required_qty'] - item['available_stock']}<br><br>")
			if msg:
				frappe.throw(msg)
		
		else:
			frappe.throw(_(f"Item Stock is not Availble please check the Stock Ledger or Stock Balance Report"))

	def check_raw_matrial_stock(self):
		"""
		Calculation The Bom from the finish goods item and is there in the reserved warehouse
		"""
		items = []
		all_stock_available = True
		if self.items:
			for item in self.items:
				po = frappe.get_doc("Purchase Order",item.purchase_order)
				if not po:
					frappe.throw(_("Purchase Order Not Found"))
				else:
					for i in po.items:
						item_code = i.fg_item
						s_item_code = i.item_code
						if item.item_code == s_item_code:
							if not item_code:
								frappe.throw(_("Finish Good Item is not found"))
							else:
								default_bom = frappe.get_value("Item", item_code, "default_bom")
								if not default_bom:
									frappe.throw(_("Bom is not found of the item {item_code}"))
								else:
									bom_doc = frappe.get_doc("BOM", default_bom)
									for bom_item in bom_doc.items:
										raw_material = bom_item.item_code
										raw_qty = bom_item.qty
										total_required_qty = flt(raw_qty * item.qty)
										available_stock = frappe.db.get_value("Bin", {"item_code": raw_material, "warehouse": po.custom_set_reserve_warehouse}, "actual_qty") or 0
										items.append({
											"service_item" : item.item_code,
											"raw_material": raw_material,
											"finished_item": item_code,
											"required_qty": total_required_qty,
											"available_stock": available_stock,
											"supplier_warehouse":po.supplier_warehouse,
											"source_warehouse":po.custom_set_reserve_warehouse
										})
									if available_stock < total_required_qty:
										all_stock_available = False
		return items, all_stock_available

	def auto_create_stock_entry(self,items):
		"""
		If the stock is available so trafer material 
		store warehouse to production warehouse
		"""	
		po_name = frappe.db.get_value("Purchase Receipt Item", {"parent": self.name}, "purchase_order")
		if not po_name:
			frappe.throw(_("No linked Purchase Order found for this Purchase Receipt."))
		
		po = frappe.get_doc("Purchase Order", po_name)

		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.posting_date = self.posting_date
		se.set_posting_time = 1
		se.from_warehouse = po.custom_set_reserve_warehouse
		se.to_warehouse = self.supplier_warehouse
		

		for mt in items:
			se_item = frappe.new_doc("Stock Entry Detail")
			se_item.s_warehouse = po.custom_set_reserve_warehouse
			se_item.t_warehouse = self.supplier_warehouse
			se_item.item_code = mt['raw_material']
			se_item.qty = mt['required_qty']
			se_item.uom = frappe.db.get_value("Item", mt['raw_material'], "stock_uom")
			se.append("items", se_item)
		se.save()
		se.submit()
	
	def auto_create_subcontracting_receipt(self):
		override_make_subcontracting_receipt(self.name, save=True,submit=True)

@frappe.whitelist()
def override_make_subcontracting_receipt(source_name, target_doc=None, save=False,submit=False):
	target_doc = make_subcontracting_receipt(source_name, target_doc)
	if not target_doc:
		return
	
	if (save or submit) and frappe.has_permission(target_doc.doctype, "create"):
		target_doc.save()

		if submit and frappe.has_permission(target_doc.doctype, "submit", target_doc):
			try:
				target_doc.submit()
			except Exception as e:
				target_doc.add_comment("Comment", _("Submit Action Failed") + "<br><br>" + str(e))
		
	

@frappe.whitelist()
def make_subcontracting_receipt(source_name, target_doc=None):
	return get_mapped_subcontracting_receipt(source_name, target_doc)


def get_mapped_subcontracting_receipt(source_name, target_doc=None):
	def update_item(source, target, source_parent):
		target.purchase_order = source_parent.purchase_order
		target.purchase_order_item = source.purchase_order_item
		target.qty = flt(source.qty) - flt(source.received_qty)
		target.amount = (flt(source.qty) - flt(source.received_qty)) * flt(source.rate)

		purchase_receipt_item = next(
			(item for item in purchase_receipt.items if item.purchase_order_item == source.purchase_order_item),
			None
		)

		if purchase_receipt_item:
			target.qty = min(flt(source.qty) - flt(source.received_qty), flt(purchase_receipt_item.qty))
			target.amount = target.qty * flt(source.rate)

	purchase_receipt = frappe.get_doc("Purchase Receipt", source_name)
	purchase_orders = list(set([d.purchase_order for d in purchase_receipt.items if d.purchase_order]))
	if not purchase_orders:
		frappe.throw(_("No Purchase Orders found in Purchase Receipt Items"))

	subcontracting_orders = frappe.get_all(
		"Subcontracting Order",
		filters={"purchase_order": ["in", purchase_orders], "docstatus": 1},
		pluck="name"
	)
	if not subcontracting_orders:
		return

	target_doc = get_mapped_doc(
		"Subcontracting Order",
		subcontracting_orders[0],
		{
			"Subcontracting Order": {
				"doctype": "Subcontracting Receipt",
				"field_map": {
					"supplier_warehouse": "supplier_warehouse",
					"set_warehouse": "set_warehouse",
				},
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Subcontracting Order Item": {
				"doctype": "Subcontracting Receipt Item",
				"field_map": {
					"name": "subcontracting_order_item",
					"parent": "subcontracting_order",
					"bom": "bom",
				},
				"postprocess": update_item,
				"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty),
			},
		},
		target_doc,
	)

	return target_doc