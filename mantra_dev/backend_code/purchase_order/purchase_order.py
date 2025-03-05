import frappe # type: ignore
from frappe.model.mapper import get_mapped_doc # type: ignore

# This function creates a "Purchase Order Expected Date" record for each item in the purchase order
# when the purchase order is approved (workflow_state is 'Approved')
@frappe.whitelist()
def create_purchase_order_expected_date(doc,method=None):
    if doc.workflow_state == 'Approved':
        for item in doc.items:
            purchase_order = frappe.new_doc("Purchase Order Expected Date")
            purchase_order.purchase_order = doc.name
            purchase_order.item_code = item.item_code
            purchase_order.qty = item.qty
            purchase_order.expected_qty = item.qty
            purchase_order.total_qty = item.qty
            purchase_order.schedule_date = item.schedule_date
            purchase_order.expected_delivery_date = item.schedule_date
            purchase_order.status=doc.workflow_state 
            purchase_order.final_expected_receive_date = item.schedule_date
            purchase_order.insert(ignore_permissions=True)

# This function cancels or updates the status of "Purchase Order Expected Date" records
# when the workflow state of the associated purchase order changes.
@frappe.whitelist()
def cancel_purchase_order_expected_date(doc,method=None):
        purchase_order_names = frappe.db.get_list("Purchase Order Expected Date", filters={'purchase_order': doc.name}, pluck='name',ignore_permissions=True)
        if purchase_order_names:
            frappe.db.set_value(
                "Purchase Order Expected Date", 
                purchase_order_names, 
                "status", 
                doc.workflow_state
            )


@frappe.whitelist()
def get_stock_details(item_code, warehouse=None):
    """
    Fetch available stock quantity for an item in a given warehouse
    and total stock across all warehouses.
    """
    stock_data = {"available_qty_in_target": 0, "total_available_stock": 0}

    # Fetch available qty in the specified warehouse
    if warehouse:
        stock_data["available_qty_in_target"] = frappe.db.get_value(
            "Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"
        ) or 0

    # Fetch total available stock across all warehouses
    total_stock = frappe.db.sql(
        """SELECT SUM(actual_qty) FROM `tabBin` WHERE item_code=%s""",
        (item_code,),
    )
    stock_data["total_available_stock"] = total_stock[0][0] if total_stock and total_stock[0][0] else 0

    return stock_data


@frappe.whitelist()
def get_po_form_details(purchase_order_id):
    if frappe.db.exists("PO Form Approval", {'purchase_order': purchase_order_id, 'docstatus': 1}):
        doc = frappe.get_doc("PO Form Approval", {'purchase_order': purchase_order_id, 'docstatus': 1})
        return doc
    else:
        return None
    

@frappe.whitelist()
def make_po_form_approval(source_name, target_doc=None, ignore_permissions=False):
    def postprocess(source, target):
        set_missing_values(source, target)

    def set_missing_values(source, target):
        target.flags.ignore_permissions = True
        target.append('price_comparison', {
            'supplier_name': source.supplier_name,
            'payment_terms': frappe.db.get_value("Supplier", source.supplier, "payment_terms") or ''
        })
    
    def update_item(source, target, source_parent):
        stock_details = get_stock_details(source.item_code, source.warehouse or None)
        target.target_warehouse_qty = stock_details['available_qty_in_target']
        target.current_stock = stock_details['total_available_stock']
        target.demand = 0
        if source.material_request:
            target.demand += frappe.db.get_value("Material Request Item", {'parent': source.material_request, 'docstatus': ['<', 2], 'item_code': source.item_code}, 'qty')
            
    doclist = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "PO Form Approval",
				"field_map": {
					"purchase_order": "name",
					"cost_center": "cost_center",
				},
			},
            "Purchase Order Item": {
				"doctype": "PO Form Item Stock",
				"field_map": {
					"item_code": "item",
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.qty
				and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
			},
		},
		target_doc,
        postprocess,
		ignore_permissions=ignore_permissions,
	)

    return doclist