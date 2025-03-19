

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

# # def permission_query_condition_meterial_request(user):
# #     user = frappe.session.user
# #     conditions = ""
    
# #     allowed_roles = ["Purchase User", "Accounts User"]
# #     user_roles = frappe.get_roles(user)
    
# #     if user == "Administrator" or any(role in user_roles for role in allowed_roles):
# #         conditions = ""
# #         return conditions
# #     else:
        
# #         if frappe.db.exists("Employee", {'user_id': user}):
           
# #             hierarchy_query = """
# #                 WITH RECURSIVE employee_hierarchy AS (
# #                     SELECT
# #                         name AS employee_id,
# #                         user_id,
# #                         0 AS level
# #                     FROM `tabEmployee`
# #                     WHERE user_id = %(logged_in_user)s

# #                     UNION ALL

# #                     SELECT
# #                         e.name AS employee_id,
# #                         e.user_id,
# #                         eh.level + 1 AS level
# #                     FROM `tabEmployee` e
# #                     INNER JOIN employee_hierarchy eh ON e.reports_to = eh.employee_id
# #                 )
# #                 SELECT user_id FROM employee_hierarchy
# #                 ORDER BY level;
# #                 """    

           
# #             hierarchy_data = frappe.db.sql(hierarchy_query, {"logged_in_user": user}, as_dict=True)
           
# #             shared_condition = f"""
# #                     EXISTS(
# #                         SELECT 1 FROM `tabDocShare` ds 
# #                         WHERE ds.share_doctype = 'Material Request'
# #                         AND ds.share_name = `tabMaterial Request`.name
# #                         AND ds.user = {frappe.db.escape(user)}
# #                     )
# #                 """if user else "1=2"
# #               # Default to false condition

           
# #             user_ids = [row['user_id'] for row in hierarchy_data]
# #             if user_ids != []:
# #                 # employee_conditions = (
# #                 #     f"IN {tuple(user_ids)}" if len(user_ids) > 1 else f"= '{user_ids[0]}'"
# #                 # )

# #                 if user_ids:
# #                     employee_conditions = f"IN {tuple(user_ids)}" if len(user_ids) > 1 else f"= '{user_ids[0]}'"
# #                 else:
# #                     employee_conditions = f"= '{user}'" 

# #                 conditions = f"""
# #                     `tabMaterial Request`.owner = {frappe.db.escape(user)}
# #                     OR `tabMaterial Request`.owner {employee_conditions}
# #                     OR ( JSON_CONTAINS(`tabMaterial Request`._assign, JSON_QUOTE({frappe.db.escape(user)})))
# #                     OR {shared_condition}
# #                 """
                
# #         else:
# #             conditions = f"""
# #                 `tabMaterial Request`.owner = {frappe.db.escape(user)}
# #                 OR ( JSON_CONTAINS(`tabMaterial Request`._assign, JSON_QUOTE({frappe.db.escape(user)})))
# #                 OR {shared_condition}
        
# #             """

# #     return conditions



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





# def permission_query_condition(user,doctype=None):
#     """Returns permission conditions dynamically based on the user's roles and the doctype."""
#     user = user or frappe.session.user

#     # Allow Administrator full access
#     if user == "Administrator":
#         return ""

#     # Define allowed roles for each doctype
#     role_permissions = {
#         "Job Opening": ["Manager - Talent Acquisition", "Team Lead - Talent Acquisition"],
#         "Job Applicant": ["Talent Acquisition Executive", "Manager - Talent Acquisition", "Team Lead - Talent Acquisition"],
#         "Job Requisition": ["Manager - Talent Acquisition", "Hiring Manager","Team Lead - Talent Acquisition","Job Requisition Approver"],
#         "Interview":["Team Lead - Talent Acquisition","Talent Acquisition Executive","Interviewer","Manager - Talent Acquisition"],
#         "Job Offer":["Talent Acquisition Executive", "Manager - Talent Acquisition", "Team Lead - Talent Acquisition","Job Offer Approver","HR OPS User"]
#     }

#     allowed_roles = role_permissions.get(doctype, [])  # Get allowed roles for the given doctype
#     user_roles = frappe.get_roles(user)

#     # Grant access if the user has at least one allowed role
#     if any(role in user_roles for role in allowed_roles):
#         return ""
#     assigned_condition = f"JSON_CONTAINS(_assign, '\"{user}\"')"
#     shared_condition = f"""
#         EXISTS (
#             SELECT 1 FROM `tabDocShare` ds 
#             WHERE ds.share_doctype = '{doctype}'
#             AND ds.share_name = `tab{doctype}`.name
#             AND ds.user = '{user}'
#         )
#     """

#     # Restrict access if the user does not have any allowed role
#     return f"({assigned_condition} OR {shared_condition})"

# def get_permission_query_conditions_for_purchase(user, doctype=None):
#     if not user or user == "Administrator":
#         return ""

#     account_manager_projects = frappe.db.get_all(
#         "Project",
#         filters={"custom_account_manager": user},
#         pluck="name"
#     )

#     project_manager_projects = frappe.db.get_all(
#         "Project",
#         filters={"custom_project_manager": user},
#         pluck="name"
#     )

#     projects = list(set(account_manager_projects + project_manager_projects))
#     if projects:
#         project_list = ", ".join(f"'{p}'" for p in projects)
#         return f"project IN ({project_list})"

#     assigned_condition = f"JSON_CONTAINS(_assign, '\"{user}\"')"
    
#     shared_condition = f"""
#         EXISTS (
#             SELECT 1 FROM `tabDocShare` ds 
#             WHERE ds.share_doctype = '{doctype}'
#             AND ds.share_name = `tab{doctype}`.name
#             AND ds.user = '{user}'
#         )
#     """
    
#     return f"({assigned_condition} OR {shared_condition})"



# def get_permission_query_conditions_for_sales(user,doctype=None):
#     if not user or user == "Administrator":
#         return ""
#     account_manager_projects = frappe.db.get_all(
#         "Project",
#         filters={"custom_account_manager": user},
#         pluck="name"
#     )

#     project_manager_projects = frappe.db.get_all(
#         "Project",
#         filters={"custom_project_manager": user},
#         pluck="name"
#     )

#     projects = list(set(account_manager_projects + project_manager_projects))

    
#     if projects:
#         customers = frappe.db.get_all("Project", 
#             filters={"name": ["in", projects]}, 
#             pluck="customer"
#         )

#         if customers:
#             customer_list = ", ".join(f"'{c}'" for c in customers)
#             return f"customer IN ({customer_list})"

#     assigned_condition = f"JSON_CONTAINS(_assign, '\"{user}\"')"
#     shared_condition = f"""
#         EXISTS (
#             SELECT 1 FROM `tabDocShare` ds 
#             WHERE ds.share_doctype = '{doctype}'
#             AND ds.share_name = `tab{doctype}`.name
#             AND ds.user = '{user}'
#         )
#     """
#     return f"({assigned_condition} OR {shared_condition})"

# def has_permission(doc, user):
#     """Checks if the user has permission to view a specific record dynamically based on its doctype."""
#     user = user or frappe.session.user

#     # Allow Administrator full access
#     if user == "Administrator":
#         return True

#     # Allow access to new records
#     if doc.is_new():
#         return True

#     condition = permission_query_condition(user,doc.doctype) or "1=1"

#     query = f"""
#         SELECT name 
#         FROM `tab{doc.doctype}`
#         WHERE ({condition}) AND name = %s
#     """
    
#     doc_list = frappe.db.sql(query, (doc.name,))
    
#     return bool(doc_list)


# def has_permission_for_sales(doc, user):
#     """Checks if the user has permission to view a specific record dynamically based on its doctype."""
#     user = user or frappe.session.user

#     # Allow Administrator full access
#     if user == "Administrator":
#         return True

#     # Allow access to new records
#     if doc.is_new():
#         return True

#     condition = get_permission_query_conditions_for_sales(user,doc.doctype) or "1=1"

#     query = f"""
#         SELECT name 
#         FROM `tab{doc.doctype}`
#         WHERE ({condition}) AND name = %s
#     """
    
#     doc_list = frappe.db.sql(query, (doc.name,))
    
#     return bool(doc_list)

# def has_permission_for_purchase(doc, user):
#     """Checks if the user has permission to view a specific record dynamically based on its doctype."""
#     user = user or frappe.session.user

#     # Allow Administrator full access
#     if user == "Administrator":
#         return True

#     # Allow access to new records
#     if doc.is_new():
#         return True

#     condition = get_permission_query_conditions_for_purchase(user,doc.doctype) or "1=1"

#     query = f"""
#         SELECT name 
#         FROM `tab{doc.doctype}`
#         WHERE ({condition}) AND name = %s
#     """
    
#     doc_list = frappe.db.sql(query, (doc.name,))
    
#     return bool(doc_list)


# def get_permission_query_conditions_for_project(user):
#     if not user or user == "Administrator":
#         return ""

#     custom_manager_condition = f"custom_account_manager = '{user}'"
#     custom_project_manager_condition = f"custom_project_manager = '{user}'"

#     assigned_condition = f"JSON_CONTAINS(_assign, '\"{user}\"')"

#     shared_condition = f"""
#         EXISTS (
#             SELECT 1 FROM tabDocShare ds 
#             WHERE ds.share_doctype = 'Project'
#             AND ds.share_name = tabProject.name
#             AND ds.user = '{user}'
#         )
#     """
#     return f"({custom_manager_condition} OR {custom_project_manager_condition} OR {assigned_condition} OR {shared_condition})"



# def has_permission_for_project(doc, user):
#     """Checks if the user has permission to view a specific record dynamically based on its doctype."""
#     user = user or frappe.session.user

#     # Allow Administrator full access
#     if user == "Administrator":
#         return True

#     # Allow access to new records
#     if doc.is_new():
#         return True
#     condition = get_permission_query_conditions_for_project(user) or "1=1"

#     query = f"""
#         SELECT name 
#         FROM `tabProject`
#         WHERE ({condition}) AND name = %s
#     """
    
#     doc_list = frappe.db.sql(query, (doc.name,))
    
#     return bool(doc_list)  # Returns True if user has permission, otherwise False


# def get_permission_query_conditions_for_travel_request(user):
#     user = user or frappe.session.user

#     # Allow full access for Administrator
#     if user == "Administrator":
#         return ""
    
#     # Restrict Travel Desk Users: Exclude 'Approval Pending by HoD' and 'Rejected' Travel Requests
#     if "Travel Desk User" in frappe.get_roles(user):
#         return "`tabTravel Request`.`workflow_state` NOT IN ('Approval Pending by HoD', 'Rejected')"
    
#     return ""

# def has_permission_for_travel_request(doc, user):
#     user = user or frappe.session.user

#     # Allow full access for Administrator
#     if user == "Administrator":
#         return True
    
#     # Restrict Travel Desk Users: Exclude 'Approval Pending by HoD' and 'Rejected' Travel Requests
#     if "Travel Desk User" in frappe.get_roles(user) and doc.workflow_state in ["Approval Pending by HoD", "Rejected"]:
#         return False
    
#     return True
    