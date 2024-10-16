import frappe
from frappe.model.document import Document

import frappe

@frappe.whitelist()
def update_darft_delivered_qty(doc, method=None):
    for dc_items in doc.items:
        if dc_items.so_detail:
            # Fetch the existing custom_draft_delivered_qty value
            qty = frappe.db.get_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty")
            print(qty)
            # Ensure qty is not None and is numeric
            if qty is None:
                qty = 0
            
            # Update the quantity
            t_qty = qty + dc_items.qty
            frappe.db.set_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty", t_qty)
    
    # Commit the transaction after all updates
    frappe.db.commit()

            
@frappe.whitelist()
def set_darft_delivered_qty(doc,method=None):
    for dc_items in doc.items:
        if dc_items.so_detail:
            qty = frappe.db.get_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty")
            print(qty)
            # Ensure qty is not None and is numeric
            if qty is None:
                qty = 0
            
            # Update the quantity
            t_qty = qty - dc_items.qty
            frappe.db.set_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty", t_qty)
            frappe.db.commit()