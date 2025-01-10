import frappe
from frappe import _
import traceback



#To create entry in erro log
@frappe.whitelist(allow_guest=True)
def errorLog(title,error,duplicate_check,reference_doctype=None,reference_name=None):


	if duplicate_check:
		query = "SELECT * from `tabError Log` WHERE error='{}' AND method='{}'".format(error,title)
		test= frappe.db.sql(query,as_dict=1)
		if len(test)!=0:
			return

	# Create a new Error Log document
	error_log = frappe.get_doc({
		"doctype": "Error Log",
		"error": error,
		"method": title,
	})
	# Insert the document into the database
	error_log.insert(ignore_permissions=True)

    #     print("Error Log created successfully!")
    # except Exception as e:
    #     # traceback.format_exc()
    #     print(f"Failed to create Error Log: {e}")

@frappe.whitelist(allow_guest=True)
def errorLogExites(title,error):
	query = "SELECT * from `tabError Log` WHERE error='{}' AND method='{}'".format(error,title)
	test= frappe.db.sql(query,as_dict=1)
	if len(test)!=0:
		return True

	return False

@frappe.whitelist(allow_guest=True)
def errorLogDelete(title,error):
	query = "DELETE FROM `tabError Log` WHERE error='{}' AND method='{}'".format(error,title)
	test= frappe.db.sql(query,as_dict=1)
	return "Record deleted"


# To create system notification
@frappe.whitelist(allow_guest=True)
def create_notification_log(
 subject: str,
 content: str,
 notification_type: str = "Alert",
 document_type: str = None,
 document_name: str = None,
 for_user: str = None
 ) -> None:
	
	"""
	Creates a notification log for a specific user or the current session user.

	Parameters:
	1. subject (str): The title or subject of the notification.
	2. content (str): The detailed content/message of the notification.
	3. notification_type (str): Type of notification (e.g., "Alert", "Warning"). Default is "Alert".
	4. document_type (str, optional): The Doctype to be opened when the notification is clicked.
	5. document_name (str, optional): The specific document to be opened when the notification is clicked.
	6. for_user (str, optional): The user for whom the notification is intended. Defaults to the current session user.
	Returns:
	None
	"""
	if not for_user:
		for_user = frappe.session.user


	notification_log = frappe.get_doc({
		"doctype": "Notification Log",
		"subject": subject,
		"email_content": content,
		"document_type": document_type,
		"document_name": document_name,
		"for_user": for_user,
		"type": notification_type
	})

	notification_log.insert(ignore_permissions=True)



@frappe.whitelist(allow_guest=True)
def ClearBenyFileProcessLog():
	query = "DELETE FROM `tabError Log` WHERE `method`='BENYPROCESSFILE'"
	test= frappe.db.sql(query,as_dict=1)
	query = "DELETE FROM `tabError Log` WHERE `method`='PAYMENTPROCESSFILE'"
	test= frappe.db.sql(query,as_dict=1) 
	return "Record deleted"

@frappe.whitelist(allow_guest=True)
def ClearBenyFileProcessLog_withTitle(title):
	query = "DELETE FROM `tabError Log` WHERE `method` like '{}%'".format(title)
	test= frappe.db.sql(query,as_dict=1)
	return "Record deleted"