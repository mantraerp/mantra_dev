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



@frappe.whitelist(allow_guest=True)
def get_app_name():
	siteurl = get_url()
	if siteurl in ["http://10.172.100.21:8001","https://mantratec.milaap.ai","http://mantratecerpstage.com:8001","http://127.0.0.1:8001"]:
		return "mantra"
	elif siteurl in ["http://10.172.100.22:8008","https://mefron.milaap.ai","http://mefronerp.com:8008","http://mefronerp.com:8003","http://10.172.100.22:8003","http://127.0.0.1:8008"]:
		return "mefron"
	elif siteurl in ["http://10.172.100.22:8000","https://mantrasmart.milaap.ai","http://mantrasmartidentityrep.com:8000","http://ibu.mantraidentity.com:8000","http://127.0.0.1:8000","https://mantrasmart.milaap.ai:8000"]:
		return "smart identity"
	elif siteurl in ["http://10.172.100.22:8001","https://mitras.milaap.ai","http://mitrasglobal.com:8002","http://127.0.0.1:8001"]:
		return "mitras global"
	elif siteurl in ["http://10.172.100.22:8002","https://mewurk.milaap.ai","http://mewurktechnologies.com:8002","http://127.0.0.1:8002"]:
		return "mewurk"
	elif siteurl in ["http://10.172.100.22:8005","https://mocula.milaap.ai","http://mocula.com:8005","http://127.0.0.1:8005"]:
		return "mocula"
	elif siteurl in ["http://10.172.100.22:8006","https://mupizo.milaap.ai","http://mupizo.com:8006","http://127.0.0.1:8006"]:
		return "mupizo"
	elif siteurl in ["http://10.172.100.22:8009","https://Smartfzco.milaap.ai","https://smartfzco.milaap.ai","http://fzco.com:8009","http://127.0.0.1:8009"]:
		return "smartfzco"
	elif siteurl in ["http://10.172.100.22:8010","https://smartfze.milaap.ai","http://fzcodubai.com:8010","http://127.0.0.1:8010"]:
		return "smartfze"	
	elif siteurl in ["http://10.172.100.22:8004","http://servico.com:8004"]:
		return "servico"
	elif siteurl in ["http://10.172.100.22:8011","https://mexcys.milaap.ai","http://mexcys_nodes:8011","http://mexcys.com:8011","http://127.0.0.1:8011"]:
		return "mexcys"

	send_error_message_to_developer("Application name not found","site url is :{}".format(siteurl))

	return '-'



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



# https://mantratec.milaap.ai/api/method/mantra.backend_code.globle.ClearBenyFileProcessLog_withTitle?title=mantra.backend_code.serialno.process_dc_item

@frappe.whitelist(allow_guest=True)
def ClearBenyFileProcessLog_withTitle(title):
	query = "DELETE FROM `tabError Log` WHERE `method` like '{}%'".format(title)
	test= frappe.db.sql(query,as_dict=1)
	return "Record deleted"