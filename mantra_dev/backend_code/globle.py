import frappe # type: ignore
from frappe import _ # type: ignore
import traceback
import requests # type: ignore
from frappe.utils import get_url # type: ignore


@frappe.whitelist(allow_guest=True)
def check_system_status():

	reply={}
	reply['UAT']="Not working"

	reply['message']=""

	if not frappe.db.get_single_value("ERP Settings", "get_system_status_notification"):
		return "System status not on"

	email_list = frappe.db.get_single_value("ERP Settings", "system_status_notification_users").replace("\n", ",")
	email_receipient = email_list.split(",")

	if len(email_receipient)==0:
		return "No email found"

# check_system_status
	reply = system_call(reply,"http://192.168.5.78:8000/login#login",'UAT')
	reply = system_call(reply,"http://192.168.5.56:8000/#login",'Smart Identity (IBU)')
	reply = system_call(reply,"http://192.168.5.56:8001/#login",'Mitras Global') 
	reply = system_call(reply,"http://192.168.5.56:8002/#login",'Mewruk')
	reply = system_call(reply,"http://192.168.5.56:8007/#login",'VAPT')
	reply = system_call(reply,"http://192.168.5.56:8008/#login",'Mefron')
	reply = system_call(reply,"http://192.168.5.56:8004/#login",'Servico')
	reply = system_call(reply,"http://192.168.5.56:8005/#login",'Mocula')
	reply = system_call(reply,"http://192.168.5.56:8006/#login",'Mupizo')
 
 
	keys = reply.keys()
	email_message_body=""
	for ky in keys:
		if ky != 'message':
			email_message_body = "{}<b>{}</b>: {}<br>".format(email_message_body,ky,reply[ky])

	email_message_body = "<br><br><br><br>{}<b>{}</b>: {}".format(email_message_body,'message',reply['message'])

	frappe.sendmail(
		recipients=email_receipient,
		subject="System status {}".format(frappe.utils.nowdate()),
		message=email_message_body
	)

	frappe.enqueue(permission_count, queue='long', timeout=10000)
	return reply

def system_call(reply,url,key):
	reply[key]="Not working"
	try:
		response = requests.post(url)
		if response.status_code == 200:
			reply[key]="Working"
	except Exception as e:
		reply[key]="Not working"
		reply['message'] = "{}<br><br><b>{} traceable error</b>:<br>{}".format(reply['message'],key,str(traceback.format_exc()))
 
	return reply

def site_base_url():
	siteurl = get_url()
	if "http://192.168.1.38:8001":
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
def order_status():
	query = """
 				SELECT status, COUNT(name) AS order_count, SUM(grand_total) AS grand_total_value, SUM(net_total) AS net_total_value
				FROM `tabSales Order`
				WHERE docstatus < 2
				GROUP BY status;
			"""
	data_list = frappe.db.sql(query,as_dict=1)	
 
	html = """
			<!DOCTYPE html>
			<html>
			<head>
				<title>Order Status</title>
				<style>
					th {
						padding: 15px;
						text-align: left;
					}
				</style>    
			</head>
			<body>

				<h2>All Order Status</h2>

				<table>
					<thead>
						<tr style="text-align: left;">
							<th>Status</th>
							<th>Total</th>
						</tr>
					</thead>
					<tbody id="order-table-body">
 			"""
 
 
	for data in data_list:
		html = """{}
			<tr>
				<th>{}</th>
				<th>{}</th>
			</tr>
  		""".format(html,data['status'],data['order_count'],data['grand_total_value'],data['net_total_value'])

 
 
	end_html = """{}
					</tbody>
				</table>
			</body>
			</html>
		""".format(html)
 
	frappe.sendmail(
		recipients=["ravi.patel@mantratec.com"],
		subject="All Order Status",
		message=html,
		as_markdown=False,
		delayed=False
	)

	return "Mail send for permission count"



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