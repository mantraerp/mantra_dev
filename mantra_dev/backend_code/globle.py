import frappe # type: ignore
from frappe import _ # type: ignore
import traceback
import requests # type: ignore
from frappe.utils import get_url # type: ignore



def create_todo(description,allocated_to,date=None,status='Open',priority='Medium',reference_type='',reference_name=''):
    
    if date==None:
        date = frappe.utils.nowdate()
    
    todo = frappe.get_doc({
        "doctype": "ToDo",
        "description": description,
        "allocated_to": allocated_to,  # Assign to user
        "status": status,
        "priority": priority,         # Options: Low, Medium, High
        "date": date,
        "reference_type": reference_type,
        "reference_name": reference_name
    })
    todo.insert(ignore_permissions=True)
    return f"ToDo created with name: {todo.name}"


def site_base_url():
	siteurl = get_url()
	if siteurl=="http://192.168.1.38:8001":
		siteurl = "https://mantratec.milaap.ai"
  
	return siteurl

def permission_count():
	query = "SELECT * from `tabCustom DocPerm`"
	test= frappe.db.sql(query,as_dict=1)
	
	frappe.sendmail(
		recipients=["ravi.patel@mantratec.com","abhishek.jain@mantratec.com"],
		subject="Document Permission Count {}".format(len(test)),
		message="This is to track permission count"
	)

	return "Mail send for permission count"


@frappe.whitelist(allow_guest=True)
def weekly_check():

	email_receipient = ['ravi.patel@mantratec.com','sajal.chandrawanshi@mantratec.com','abhishek.jain@mantratec.com']
	email_message_body = """<br> This mail is to reminder for weelky check point list.
		<br> 1. ERP auto backup is work based on set numbers.
 	"""

 
	frappe.sendmail(
		recipients=email_receipient,
		subject="Weekly check points {}".format(frappe.utils.nowdate()),
		message=email_message_body
	)

	return True

#To create entry in erro log
@frappe.whitelist(allow_guest=True)
def errorLog(title,error,duplicate_check=False,reference_doctype=None,reference_name=None):


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


#To clear process beny file name
@frappe.whitelist(allow_guest=True)
def ClearBenyFileProcessLog():
	frappe.enqueue(clear_beny_file_process_log, queue='long', timeout=10000)
	return True

@frappe.whitelist()
def clear_beny_file_process_log():   
    
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