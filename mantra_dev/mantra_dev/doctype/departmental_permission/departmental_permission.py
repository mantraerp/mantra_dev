# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DepartmentalPermission(Document):
	# pass
    
    def on_change(self):

        if self.user:
            
            emp_id = frappe.db.get_value("Employee",{"user_id":self.user},"name")
            sp_emp = frappe.db.get_value("Sales Person",{"employee":emp_id},"parent_sales_person")
           
            
            user_permissions_warehouse = frappe.get_all(
                    "User Permission",
                    filters={"user": self.user, "allow": "Warehouse"},
                    fields=["name", "for_value"]
                )
            
            user_permissions_item = frappe.get_all(
                    "User Permission",
                    filters={"user": self.user, "allow": "Item"},
                    fields=["name", "for_value"]
                )
            
            
            
            if self.warehouse == []:
                

                for permission in user_permissions_warehouse:
                    warehouse = permission["for_value"]

                    
                    
                    sp_warehouse_exists = frappe.db.exists("Departmental Permission Warehouse",{"parent":sp_emp,"parenttype":"Sales Person","warehouse":warehouse})


                    if not sp_warehouse_exists:
                        frappe.delete_doc("User Permission", permission["name"])
                        frappe.db.commit()
                
                
                
                
            for w in self.warehouse:

                if not frappe.db.exists("User Permission",{"user":self.user,"allow":"Warehouse","for_value":w.warehouse}):
                    doc = frappe.new_doc("User Permission")
                    doc.user = self.user	
                    doc.allow = "Warehouse"
                    doc.for_value = w.warehouse
                    doc.save()


              

                for permission in user_permissions_warehouse:
                    warehouse = permission["for_value"]

                    warehouse_exists = frappe.db.exists(
                        "Departmental Permission Warehouse", 
                        {"warehouse": warehouse, "parent": self.name,"parenttype":"Departmental Permission"}
                    )
                    
                    sp_warehouse_exists = frappe.db.exists("Departmental Permission Warehouse",{"parent":sp_emp,"parenttype":"Sales Person","warehouse":warehouse})


                    if not warehouse_exists and not sp_warehouse_exists:
                        frappe.delete_doc("User Permission", permission["name"])
                        frappe.db.commit()  




            
            
            if self.items == []:
                
                for permission in user_permissions_item:
                    items = permission["for_value"]

                   
                    
                    sp_item_exists = frappe.db.exists("Department Permission Item",{"parent":sp_emp,"parenttype":"Sales Person","item":items})

                    if not sp_item_exists:
                        frappe.delete_doc("User Permission", permission["name"])
                        frappe.db.commit()  
                
                
            for item in self.items:

                if not frappe.db.exists("User Permission",{"user":self.user,"allow":"Item","for_value":item.item}):
                    doc = frappe.new_doc("User Permission")
                    doc.user = self.user	
                    doc.allow = "Item"
                    doc.for_value = item.item
                    doc.save()
                


                

                for permission in user_permissions_item:
                    items = permission["for_value"]

                    items_exists = frappe.db.exists(
                        "Department Permission Item", 
                        {"item": items, "parent": self.name,"parenttype":"Departmental Permission"}
                    )
                    
                    sp_item_exists = frappe.db.exists("Department Permission Item",{"parent":sp_emp,"parenttype":"Sales Person","item":items})

                    if not items_exists and not sp_item_exists:
                        frappe.delete_doc("User Permission", permission["name"])
                        frappe.db.commit()  




    def after_delete(self):

        
        if self.warehouse:
            




            for wh in self.warehouse:
                user_permission_name = frappe.db.exists("User Permission", {
                    "user": self.user,
                    "allow": "Warehouse",
                    "for_value": wh.warehouse
                })

               
                if user_permission_name:
                    frappe.delete_doc("User Permission", user_permission_name)
                    frappe.db.commit()

        if self.items:
            for item in self.items:
                user_permission_name_item = frappe.db.exists("User Permission", {
                    "user": self.user,
                    "allow": "Item",
                    "for_value": item.item
                })
                
                if user_permission_name_item:
                    frappe.delete_doc("User Permission", user_permission_name_item)
                    frappe.db.commit()


            





             
                  





import frappe
import json



@frappe.whitelist()
def get_items_for_products(selected_products):
  
    selected_products=json.loads(selected_products)

    items_list = []
  

   
    for product in selected_products:
        
        child_items = frappe.get_all(
            "Product Item",
            filters={"parent": product['product']}, 
            fields=["item_code"],
            pluck="item_code"
        ) or []  
      

        items_list.extend(child_items)


    return items_list

