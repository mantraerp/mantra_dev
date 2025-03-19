# import frappe


# def on_change_sales_person(self,method):
        


#     user_email = frappe.db.get_value("Employee",self.employee,"user_id")


#     if user_email and self.is_group:
        
#         for w in self.custom_warehouse:

#             if not frappe.db.exists("User Permission",{"user":user_email,"allow":"Warehouse","for_value":w.warehouse}):
#                 doc = frappe.new_doc("User Permission")
#                 doc.user = user_email	
#                 doc.allow = "Warehouse"
#                 doc.for_value = w.warehouse
#                 doc.save()


#             user_permissions = frappe.get_all(
#                 "User Permission",
#                 filters={"user": user_email, "allow": "Warehouse"},
#                 fields=["name", "for_value"]
#             )

#             for permission in user_permissions:
#                 warehouse = permission["for_value"]

#                 warehouse_exists = frappe.db.exists(
#                     "Departmental Permission Warehouse", 
#                     {"warehouse": warehouse, "parent": self.name,"parenttype":"Sales Person"}
#                 )

#                 if not warehouse_exists:
#                     frappe.delete_doc("User Permission", permission["name"])
#                     frappe.db.commit()  

          






#         for item in self.custom_items:

#             if not frappe.db.exists("User Permission",{"user":user_email,"allow":"Item","for_value":item.item}):
#                 doc = frappe.new_doc("User Permission")
#                 doc.user = user_email	
#                 doc.allow = "Item"
#                 doc.for_value = item.item
#                 doc.save()
            


#             user_permissions = frappe.get_all(
#                 "User Permission",
#                 filters={"user": user_email, "allow": "Item"},
#                 fields=["name", "for_value"]
#             )

#             for permission in user_permissions:
#                 items = permission["for_value"]

#                 items_exists = frappe.db.exists(
#                     "Department Permission Item", 
#                     {"item": items, "parent": self.name,"parenttype":"Sales Person"}
#                 )

#                 if not items_exists:
#                     frappe.delete_doc("User Permission", permission["name"])
#                     frappe.db.commit()  







    

#     if self.is_group:
#         sales_person_list = frappe.get_all("Sales Person",{"parent_sales_person":self.name},pluck="name")

        
#         for i in sales_person_list:

#             sales_person_doc = frappe.get_doc("Sales Person",i)
#             if sales_person_doc.employee:
#                 user_email = frappe.db.get_value("Employee",sales_person_doc.employee,"user_id")

#                 ware_list = frappe.db.get_all("Departmental Permission Warehouse",{"parent":sales_person_doc.parent_sales_person},['warehouse'])
                
#                 user_permissions_warehouse = frappe.get_all(
#                         "User Permission",
#                         filters={"user": user_email, "allow": "Warehouse"},
#                         fields=["name", "for_value"]
#                     )
                
                
#                 if ware_list == []:
              

#                     for permission in user_permissions_warehouse:
#                         warehouse = permission["for_value"]

                 
#                         dp_warehouse_exists = frappe.db.exists("Departmental Permission Warehouse",{"parent":user_email,"parenttype":"Departmental Permission","warehouse":warehouse})


#                         if not dp_warehouse_exists:
#                             frappe.delete_doc("User Permission", permission["name"])
#                             frappe.db.commit()

#                 for w in ware_list:

#                     if not frappe.db.exists("User Permission",{"user":user_email,"allow":"Warehouse","for_value":w.warehouse}):
#                         doc = frappe.new_doc("User Permission")
#                         doc.user = user_email	
#                         doc.allow = "Warehouse"
#                         doc.for_value = w.warehouse
#                         doc.save()
#                         sales_person_doc.save()


#                     for permission in user_permissions_warehouse:
#                         warehouse = permission["for_value"]

#                         warehouse_exists = frappe.db.exists(
#                             "Departmental Permission Warehouse", 
#                             {"warehouse": warehouse, "parent": self.name,"parenttype":"Sales Person"}
#                         )
                        
#                         dp_warehouse_exists = frappe.db.exists("Departmental Permission Warehouse",{"parent":user_email,"parenttype":"Departmental Permission","warehouse":warehouse})


#                         if not warehouse_exists and not dp_warehouse_exists:
#                             frappe.delete_doc("User Permission", permission["name"])
#                             sales_person_doc.save()
#                             frappe.db.commit()  


#                 item_list = frappe.db.get_all("Department Permission Item",{"parent":sales_person_doc.parent_sales_person},['item'])

                
                
#                 user_permissions_item = frappe.get_all(
#                     "User Permission",
#                     filters={"user": user_email, "allow": "Item"},
#                     fields=["name", "for_value"]
#                 )
                
#                 if item_list == []:
          

#                     for permission in user_permissions_item:
#                         items = permission["for_value"]

                   
                        
#                         dp_item_exists = frappe.db.exists("Department Permission Item",{"parent":user_email,"parenttype":"Departmental Permission","item":items})


#                         if not dp_item_exists:
#                             frappe.delete_doc("User Permission", permission["name"])
#                             frappe.db.commit()
                
                
#                 for item in item_list:
#                     if not frappe.db.exists("User Permission",{"user":user_email,"allow":"Item","for_value":item.item}):
#                         doc = frappe.new_doc("User Permission")
#                         doc.user = user_email	
#                         doc.allow = "Item"
#                         doc.for_value = item.item
#                         doc.save()
#                         sales_person_doc.save()
                    



#                     for permission in user_permissions_item:
#                         items = permission["for_value"]

#                         items_exists = frappe.db.exists(
#                             "Department Permission Item", 
#                             {"item": items, "parent": self.name,"parenttype":"Sales Person"}
#                         )
                        
#                         dp_item_exists = frappe.db.exists("Department Permission Item",{"parent":user_email,"parenttype":"Departmental Permission","item":items})


                        

#                         if not items_exists and not dp_item_exists:
#                             frappe.delete_doc("User Permission", permission["name"])
#                             sales_person_doc.save()
#                             frappe.db.commit()
    






# def before_save(self,method):

#     if self.parent_sales_person and not self.is_group:
#         ware_list = frappe.db.get_all("Departmental Permission Warehouse",{"parent":self.parent_sales_person},['warehouse'])
       

#         user_email = frappe.db.get_value("Employee",self.employee,"user_id")
#         if user_email:
#             for w in ware_list:

#                     if not frappe.db.exists("User Permission",{"user":user_email,"allow":"Warehouse","for_value":w.warehouse}):
#                         doc = frappe.new_doc("User Permission")
#                         doc.user = user_email	
#                         doc.allow = "Warehouse"
#                         doc.for_value = w.warehouse
#                         doc.save()



#         item_list = frappe.db.get_all("Department Permission Item",{"parent":self.parent_sales_person},['item'])
#         if user_email:
#             for item in item_list:

#                 if not frappe.db.exists("User Permission",{"user":user_email,"allow":"Item","for_value":item.item}):
#                     doc = frappe.new_doc("User Permission")
#                     doc.user = user_email	
#                     doc.allow = "Item"
#                     doc.for_value = item.item
#                     doc.save()












