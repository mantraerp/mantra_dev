import frappe
from frappe.model.document import Document

@frappe.whitelist()
def make_stock_entry(doc, method=None):
    # pass
    custom_setting=frappe.db.get_single_value("Custom Settings", "auto_create_stock_entry")
    if custom_setting==1:
        vendor_setting=frappe.get_value("Supplier",doc.supplier,"custom_auto_create_stock_entry")
        if vendor_setting==1:
    # Debug message to ensure the function is triggered
    
    
            # Create a new Stock Entry document
            stock_en = frappe.new_doc("Stock Entry")
            
            # Copy fields from Subcontracting Receipt to Stock Entry
            stock_en.stock_entry_type = "Send to Subcontractor"
            stock_en.posting_date = doc.posting_date
            stock_en.posting_time = doc.posting_time
            stock_en.items = []
            sub_order=''
            # Iterate through items in the Subcontracting Receipt
            for item in doc.supplied_items:
                if not item.get('rm_item_code'):
                    frappe.throw("Item code is missing in one of the items.")
                
                # Verify if the item exists in the 'Raw Materials Supplied' table of the Subcontracting Order
                raw_materials = frappe.db.exists(
                    'Subcontracting Order Supplied Item',
                    {'parent': item.subcontracting_order, 'rm_item_code': item.rm_item_code}
                )
                
                if not raw_materials:
                    frappe.throw(f"row material not found")
                
                set_warehouse = frappe.db.get_value("Subcontracting Order", item.subcontracting_order, "set_reserve_warehouse")
                t_warehouse = frappe.db.get_value("Subcontracting Order", item.subcontracting_order, "supplier_warehouse")
                
                # Append item to Stock Entry
                se_item = stock_en.append('items', {})
                se_item.item_code = item.rm_item_code
                se_item.item_name = item.item_name
                se_item.qty = item.required_qty
                se_item.s_warehouse = set_warehouse
                se_item.t_warehouse = t_warehouse
                se_item.subcontracted_item=item.main_item_code
                sub_order=item.subcontracting_order
            stock_en.subcontracting_order=sub_order
            
            # Attempt to insert and submit the Stock Entry
            try:
                stock_en.insert()
                # stock_en.subcontracting_order=sub_order
                # stock_en.save()
                stock_en.submit()
                frappe.db.commit()
                frappe.msgprint(f"Stock Entry {stock_en.name} created successfully.")
            except Exception as e:
                frappe.log_error(message=str(e), title="Error in make_stock_entry")
                frappe.throw(f"An error occurred while creating the Stock Entry: {str(e)}")
