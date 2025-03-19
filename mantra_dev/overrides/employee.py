# import frappe
# from frappe.utils import get_url


# @frappe.whitelist()
# def create_user(employee, user=None, email=None):
#     emp = frappe.get_doc("Employee", employee)

#     employee_name = emp.employee_name.split(" ")
#     middle_name = last_name = ""

#     if len(employee_name) >= 3:
#         last_name = " ".join(employee_name[2:])
#         middle_name = employee_name[1]
#     elif len(employee_name) == 2:
#         last_name = employee_name[1]

#     first_name = employee_name[0]

#     if email:
#         emp.prefered_email = email

#     user = frappe.new_doc("User")
#     user.update(
#         {
#             "name": emp.employee_name,
#             "email": emp.prefered_email,
#             "enabled": 1,
#             "first_name": first_name,
#             "middle_name": middle_name,
#             "last_name": last_name,
#             "gender": emp.gender,
#             "birth_date": emp.date_of_birth,
#             "phone": emp.cell_number,
#             "bio": emp.bio,
#         }
#     )
#     user.insert()
#     emp.user_id = user.name
#     emp.save()
#     # return user.name




#     if not frappe.db.exists("Departmental Permission",{"user":user.email}):
#         emplyee_doc = frappe.get_doc("Employee",{"user_id":user.email})

#         if emplyee_doc:
#             product_list = frappe.db.get_all("Product Departments",{"department": ["in", emp.department],},pluck="parent")
#             warehouse_id = frappe.db.get_value("Department",{"name":emp.department},['name'])
#             material_request_type = frappe.db.get_all("Material Request Type Purpose",{"parent":emp.department,"parenttype":"Department"},pluck='material_request_type')

            
            

#             department_doc = frappe.new_doc("Departmental Permission")


#             department_doc.department = emp.department
#             department_doc.user = emp.user_id

#             if product_list:
#                 for product in product_list:
#                     department_doc.append("product",{"product":product})
#                     item_list = frappe.db.get_all("Product Item",{"parent":product},['item_code'],pluck='item_code')
#                     for items in item_list:
                       
#                         department_doc.append("items",{"item":items})
#             if warehouse_id:
#                 warehouse_list = frappe.db.get_all("Departmental Permission Warehouse",filters={"parent":emp.department},fields=['warehouse'], pluck="warehouse")
#                 for warehouse in warehouse_list:
                   
#                     department_doc.append("warehouse",{"warehouse":warehouse})

#             if material_request_type:
#                 for purpose in material_request_type:
#                     department_doc.append("material_request_type",{"material_request_type":purpose})

            
           

#             department_doc.save()
#             frappe.db.commit()

#     return user.name
    



