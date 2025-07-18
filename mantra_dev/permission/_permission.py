

# import frappe

# def get_permission_query_conditions_employee(user):
#     # pass
#     allowed_roles = ["Purchase User", "Accounts User","System Manager"]
#     user_roles = frappe.get_roles(user)
#     if not user:
#         user = frappe.session.user
#     if user == "Administrator"or any(role in user_roles for role in allowed_roles):
#         return None
    
    

#     return f"`tabEmployee`.`user_id` = '{user}'"

# def has_permission_employee(doc,user):
   
    
#     if not user:
#         user = frappe.session.user

#     if user == "Administrator":
#         return None

    
#     if doc.is_new():
#         return True
    

#     condition = get_permission_query_conditions_employee(user) or "1=1"

#     query = f"""SELECT name 
#             FROM `tabEmployee`
#             WHERE ({condition}) 
#             and name = '{doc.name}'"""
        
#     emp_list = frappe.db.sql(query)
#     if emp_list:
#         return True
#     else:
#         return False   


# def get_permission_query_conditions_material_request(doc, user):
#     if not user:
#         user = frappe.session.user

#     if user == "Administrator":
#         return True
    
#     if doc.is_new():
#         return True
   
#     condition = permission_query_condition_meterial_request(user) or "1=1"
#     query = f"""SELECT name 
#         FROM `tabMaterial Request`
#         WHERE ({condition}) 
#         and name = '{doc.name}'"""
    
#     doc_list = frappe.db.sql(query)
#     if doc_list:
#         return True
#     else:
#         return False





# def permission_query_condition_meterial_request(user):
#     user = frappe.session.user
#     conditions = ""

#     allowed_roles = ["Purchase User", "Accounts User"]
#     user_roles = frappe.get_roles(user)

#     # Allow full access to admin or specific roles
#     if user == "Administrator" or any(role in user_roles for role in allowed_roles):
#         return ""

#     if frappe.db.exists("Employee", {'user_id': user}):
#         # Recursive query to fetch user hierarchy
#         hierarchy_query = """
#             WITH RECURSIVE employee_hierarchy AS (
#                 SELECT name AS employee_id, user_id, 0 AS level
#                 FROM `tabEmployee`
#                 WHERE user_id = %(logged_in_user)s

#                 UNION ALL

#                 SELECT e.name AS employee_id, e.user_id, eh.level + 1 AS level
#                 FROM `tabEmployee` e
#                 INNER JOIN employee_hierarchy eh ON e.reports_to = eh.employee_id
#             )
#             SELECT user_id FROM employee_hierarchy ORDER BY level;
#         """

#         hierarchy_data = frappe.db.sql(hierarchy_query, {"logged_in_user": user}, as_dict=True)
#         user_ids = [row['user_id'] for row in hierarchy_data if row['user_id']]

#         # Prevent invalid IN () clause
#         if user_ids:
#             employee_conditions = f"IN {tuple(user_ids)}" if len(user_ids) > 1 else f"= '{user_ids[0]}'"
#         else:
#             employee_conditions = f"= '{user}'"  # Default to self if hierarchy is empty

#         # Prevent None values in SQL
#         shared_condition = f"""
#             EXISTS(
#                 SELECT 1 FROM `tabDocShare` ds 
#                 WHERE ds.share_doctype = 'Material Request'
#                 AND ds.share_name = `tabMaterial Request`.name
#                 AND ds.user = {frappe.db.escape(user)}
#             )
#         """ if user else "1=2"

#         # Construct query
#         conditions = f"""
#             (`tabMaterial Request`.owner = {frappe.db.escape(user)}
#             OR `tabMaterial Request`.owner {employee_conditions}
#             OR JSON_CONTAINS(`tabMaterial Request`._assign, JSON_QUOTE({frappe.db.escape(user)}))
#             OR {shared_condition})
#         """

#     else:
#         shared_condition = f"""
#             EXISTS(
#                 SELECT 1 FROM `tabDocShare` ds 
#                 WHERE ds.share_doctype = 'Material Request'
#                 AND ds.share_name = `tabMaterial Request`.name
#                 AND ds.user = {frappe.db.escape(user)}
#             )
#         """ if user else "1=2"

#         conditions = f"""
#             (`tabMaterial Request`.owner = {frappe.db.escape(user)}
#             OR JSON_CONTAINS(`tabMaterial Request`._assign, JSON_QUOTE({frappe.db.escape(user)}))
#             OR {shared_condition})
#         """

#     return conditions



