import frappe

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
def get_stock_details(item_code, warehouse):
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
            