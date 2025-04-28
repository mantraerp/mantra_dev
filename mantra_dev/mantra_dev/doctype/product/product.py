# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore


class Product(Document):
    def before_save(self):
        for i in self.items:
            if not frappe.db.exists("User Permission",{"user":self.product_owner,"allow":"Item","for_value":i.item_code}):

                doc = frappe.new_doc("User Permission")
                doc.user = self.product_owner	
                doc.allow = "Item"
                doc.for_value = i.item_code
                doc.save()

        for i in self.items:
            if not frappe.db.exists("User Permission",{"user":self.product_manager,"allow":"Item","for_value":i.item_code}):

                doc = frappe.new_doc("User Permission")
                doc.user = self.product_manager	
                doc.allow = "Item"
                doc.for_value = i.item_code
                doc.save()





@frappe.whitelist()
def product_change_events(item_code,name):
    dp_name = frappe.db.get_all("Departmental Product Permission Table",{"product":name,'parenttype':"Departmental Permission"},['parent'],pluck='parent')

    
    
    for i in dp_name:
        doc_dp = frappe.get_doc("Departmental Permission",i)
        dpname =frappe.db.get_all("Departmental Product Permission Table",{"parent":i,'parenttype':"Departmental Permission"},['product'],pluck='product')
        item_exists = False
        for j in dpname:
            
            if frappe.db.exists("Product Item",{"item_code":item_code,"parent":j,'parenttype':"Departmental Permission"})and j != name:
                
                item_exists = True
                break
                    
        
            else:
                child_doc = frappe.get_all("Department Permission Item", {"parent": i, "item": item_code,'parenttype':"Departmental Permission"}, ["name"])
                if child_doc:
                    for item in child_doc:
                        frappe.delete_doc("Department Permission Item", item["name"])
                        doc_dp.save()


                    break


    sales_person_product = frappe.db.get_all("Departmental Product Permission Table",{"product":name,"parenttype":"Sales Person"},['parent'],pluck='parent')

    
    
    for i in sales_person_product:
        doc_sp = frappe.get_doc("Sales Person",i)
        spname =frappe.db.get_all("Departmental Product Permission Table",{"parent":i,"parenttype":"Sales Person"},['product'],pluck='product')
        item_exists = False
        for j in spname:
            
            if frappe.db.exists("Product Item",{"item_code":item_code,"parent":j,"parenttype":"Sales Person"})and j != name:
                
                item_exists = True
                break
                    
        
            else:
                child_doc = frappe.get_all("Department Permission Item", {"parent": i, "item": item_code,"parenttype":"Sales Person"}, ["name"])
                if child_doc:
                    for item in child_doc:
                        frappe.delete_doc("Department Permission Item", item["name"])
                        doc_sp.save()


                    break

                   







@frappe.whitelist()
def product_change_events_add(item_code,name):
    dp_name = frappe.db.get_all("Departmental Product Permission Table",{"product":name,'parenttype':"Departmental Permission"},['parent'],pluck='parent')
    
    for i in dp_name:
        doc_dp = frappe.get_doc("Departmental Permission",i)



        if not frappe.db.exists("Department Permission Item",{"item":item_code,"parent":doc_dp.name,'parenttype':"Departmental Permission"}) and doc_dp.user: 

            doc_dp.append("items",{"item":item_code})

            doc_dp.save()



    sales_person_product = frappe.db.get_all("Departmental Product Permission Table",{"product":name,"parenttype":"Sales Person"},pluck='parent')
    
    for i in sales_person_product:
        doc_sp = frappe.get_doc("Sales Person",i)



        if not frappe.db.exists("Department Permission Item",{"item":item_code,"parent":doc_sp.name,"parenttype":"Sales Person"}): 

            doc_sp.append("custom_items",{"item":item_code})

            doc_sp.save()
















import json

import frappe
@frappe.whitelist()
def handle_stock_entry_type_changes(removed_department, added_department, doc_name,doc_items):
    if isinstance(added_department, str):
        added_department = json.loads(added_department)
    if isinstance(removed_department, str):
        removed_department = json.loads(removed_department)

    if isinstance(doc_name, str):
        doc_name = json.loads(doc_name)

    if isinstance(doc_items, str):
        doc_items = json.loads(doc_items)
    result = {}


    employee_user = frappe.db.get_all("Employee",{"department":doc_name},pluck='user_id')

    


    if added_department:
        for department in added_department:
            department_permission_list = frappe.db.get_all(
                "Departmental Permission", 
                filters={"department": department}, 
                pluck="name"
            )
           

            for permission_name in department_permission_list:
                doc = frappe.get_doc("Departmental Permission", permission_name)

                if not frappe.db.exists("Departmental Product Permission Table", {"parent": permission_name, "product": doc_name}):
                    doc.append("product", {"product": doc_name})

                 

                    for item in doc_items:
                        if not frappe.db.exists("Department Permission Item", {"parent": permission_name, "item": item['item_code'], "parenttype": "Departmental Permission"}):
                            doc.append("items", {"item": item['item_code']})  

                        doc.save() 






    if removed_department:
        for department in removed_department:
            department_permission_list = frappe.db.get_all(
                "Departmental Permission",
                filters={"department": department},
                pluck="name"
            )

            for permission_name in department_permission_list:

                doc = frappe.get_doc("Departmental Permission", permission_name)


                for product in doc.get("product"):
                    if product.product == doc_name:
                        doc.remove(product)

                
                
                pi = frappe.db.get_all("Product Item",{"parent":doc_name},pluck="item_code")


               
                product_list = frappe.db.get_all("Departmental Product Permission Table",{"parent":permission_name,"parenttype":"Departmental Permission"},pluck="product")


                

                pr_list = []
                for i in product_list:
                    if i != doc_name:
                        pr_list.append(i)


                for p in pi:
                    for row in doc.get("items"):
                
                        if row.item == p:
                            if not frappe.db.exists(
                                "Product Item",
                                {"parent": ["in", pr_list], "item_code": p}
                            ):
                                doc.remove(row)
                doc.save()
               




@frappe.whitelist()
def get_bom_item_list(selected_bom):
    doc = frappe.get_all("BOM Item",{"parent":selected_bom},['item_name','item_code','qty'])
    return doc



@frappe.whitelist()
def get_bom_list(item_code):
    doc = frappe.get_all("BOM",{"item":item_code,},['name','is_default','is_active','docstatus'])
    return doc





@frappe.whitelist()
def get_purpose_list(user):
    if user != "Administrator":
        if frappe.db.exists("Departmental Permission",{"user":user}):
            doc = frappe.get_all("Material Request Type Purpose",{"parent":user,"parenttype":"Departmental Permission"},pluck='material_request_type',distinct=True)
        else:
            doc = ["Purchase","Material Transfer","Material Issue","Material Receipt","Manufacture","Customer Provided"]
        return doc