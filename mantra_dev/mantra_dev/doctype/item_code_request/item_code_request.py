# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ItemCodeRequest(Document):
    
    def validate(doc):
        if doc.status=="Completed":
            if doc.new_item_code:
                print("New Item code added")
            else:
                frappe.throw("You Can't set Completed status, Please add new item-code") 
        if doc.status=="Approved":
            if doc.new_item_code:
                print("New Item code added")
            else:
                frappe.throw("You Can't set Approved status, Please add new item-code") 
                 
            
            
    def before_submit(doc):
        if doc.status!="Approved":
            frappe.throw("Without Approve you can't Submit this Document")
            
    def on_submit(doc):
        parent_doc = frappe.get_doc(doc.form_type, doc.sales_order_id)
        for child in parent_doc.get("items"):
            if child.name == doc.line_id:
                    child.item_code = doc.new_item_code
        parent_doc.save()
        frappe.db.commit()
