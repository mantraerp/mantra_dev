# import frappe



# def before_save(self,method):
#     # pass


#     if self.department and self.user_id:
#         stock_entry_type_list = frappe.db.get_all("Departmental Stock Entry Type",{"parent":self.department},pluck='stock_entry_type')
#         for i in stock_entry_type_list:
#             if not frappe.db.exists("User Permission",{"user":self.user_id,"allow":"Stock Entry Type","for_value":i}):
#                 doc = frappe.new_doc("User Permission")
#                 doc.user = self.user_id	
#                 doc.allow = "Stock Entry Type"
#                 doc.for_value = i
#                 doc.save()


    

    

#     if self.user_id and self.department:
       
       
       
#         if not frappe.db.exists("Departmental Permission",{"user":self.user_id}):
#             product_list = frappe.db.get_all("Product Departments",{"department": ["in", self.department],},pluck="parent")

#             warehouse_name = frappe.db.get_all("Departmental Permission Warehouse",filters={"parent":self.department,"parenttype":"Department"},fields=['warehouse'], pluck="warehouse")

#             material_request_type = frappe.db.get_all("Material Request Type Purpose",{"parent":self.department,"parenttype":"Department"},pluck='material_request_type')
            
            

#             doc = frappe.new_doc("Departmental Permission")


#             doc.department = self.department
#             doc.user = self.user_id

#             if product_list:
#                 for product in product_list:
#                     doc.append("product",{"product":product})
#                     item_list = frappe.db.get_all("Product Item",{"parent":product},['item_code'],pluck='item_code')
#                     for items in item_list:
#                         doc.append("items",{"item":items})
           
#             if warehouse_name:
#                 for warehouse in warehouse_name:
                   
#                     doc.append("warehouse",{"warehouse":warehouse})

#             if material_request_type:
#                 for purpose in material_request_type:
#                     doc.append("material_request_type",{"material_request_type":purpose})

            
           

#             doc.save()
#             frappe.db.commit()
            
