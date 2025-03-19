

# import frappe
# import json

# @frappe.whitelist()
# def handle_warehouse_changes(added_warehouse, removed_warehouse, doc_name):
#     if isinstance(added_warehouse, str):
#         added_warehouse = json.loads(added_warehouse)
#     if isinstance(removed_warehouse, str):
#         removed_warehouse = json.loads(removed_warehouse)

#     if isinstance(doc_name, str):
#         doc_name = json.loads(doc_name)

#     result = {}





#     if removed_warehouse:
#         dp_records = frappe.get_all(
#             "Departmental Permission",
#             filters={"department": doc_name},
#             pluck="name"
#         )

#         for dp_name in dp_records:
#             dp_doc = frappe.get_doc("Departmental Permission", dp_name)

#             child_warehouses = dp_doc.get("warehouse")

#             updated_warehouses = [row for row in child_warehouses if row.warehouse not in removed_warehouse]

#             dp_doc.set("warehouse", updated_warehouses)

#             dp_doc.save() 

#         result["removed_warehouse"] = removed_warehouse



#     if added_warehouse:
#         result["added_warehouse"] = added_warehouse


#         dp_records1 = frappe.get_all("Departmental Permission", {"department": doc_name}, pluck="name")
      

#         for dp_name in dp_records1:
#             dp_doc = frappe.get_doc("Departmental Permission", dp_name)



           
#             for warehouse in added_warehouse:
#                 if not frappe.db.exists("Departmental Permission Warehouse",{"warehouse":warehouse,"parent":dp_doc.name,"parenttype": "Departmental Permission"}) and dp_doc.user:
#                     dp_doc.append("warehouse", {"warehouse": warehouse})

#             dp_doc.save()  

           

#     return result








# import frappe
# @frappe.whitelist()
# def handle_stock_entry_type_changes(added_stock_entry_type, removed_stock_entry_type, doc_name):
#     if isinstance(added_stock_entry_type, str):
#         added_stock_entry_type = json.loads(added_stock_entry_type)
#     if isinstance(removed_stock_entry_type, str):
#         removed_stock_entry_type = json.loads(removed_stock_entry_type)

#     if isinstance(doc_name, str):
#         doc_name = json.loads(doc_name)

#     result = {}


#     employee_user = frappe.db.get_all("Employee",{"department":doc_name},pluck='user_id')


#     if added_stock_entry_type and employee_user:
        

#         for i in added_stock_entry_type:
#             for j in employee_user:
#                 if j  and not frappe.db.exists("User Permission",{"user":j,"allow":"Stock Entry Type","for_value":i}):
#                     doc = frappe.new_doc("User Permission")
#                     doc.user = j	
#                     doc.allow = "Stock Entry Type"
#                     doc.for_value = i
#                     doc.save()



#     if removed_stock_entry_type:
#         user_perm_list = frappe.get_all(
#             "User Permission",
#             filters={
#                 "user": ["in", employee_user], 
#                 "for_value": ["in", removed_stock_entry_type],
#                 "allow":"Stock Entry Type"
#             },
#             pluck="name"
#         )

#         for i in user_perm_list:
#             frappe.delete_doc("User Permission", i)
#             frappe.db.commit()



# @frappe.whitelist()
# def material_request_type_list(department,purpose):
#     d_user = frappe.db.get_all("Departmental Permission",{"department":department},pluck="user")
#     for i in d_user:
#         doc = frappe.get_doc("Departmental Permission",i)

#         if not frappe.db.exists("Material Request Type Purpose",{"parent":i,"parenttype":"Departmental Permission","material_request_type":purpose}) and doc.user:
#             doc.append("material_request_type", {"material_request_type": purpose})
#         doc.save()
#         frappe.db.commit()



        





# @frappe.whitelist()
# def remove_material_request_type(department, purpose):
#     d_user = frappe.db.get_all("Departmental Permission", {"department": department}, pluck="user")
    
#     for i in d_user:
#         doc = frappe.get_doc("Departmental Permission", i)

#         for row in doc.get("material_request_type"):
#             if row.material_request_type == purpose:
#                 doc.remove(row)
#                 doc.save()
                
#                 frappe.db.commit()
    


