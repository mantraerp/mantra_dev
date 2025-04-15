import frappe # type: ignore
from frappe import _ # type: ignore
import traceback
import requests # type: ignore
import re
import os
from datetime import datetime, timedelta
from mantra_dev.backend_code.globle import errorLog,errorLogExites,site_base_url # type: ignore


employee_mail = ['hrops@mantratec.com','anil.vadhel@mantratec.com','mukund.kotadia@mantratec.com','anurag@mantratec.com','ravi.patel@mantratec.com']



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
	reply = system_call(reply,"http://192.168.5.56:8003/#login",'Mefron')
	reply = system_call(reply,"http://192.168.5.56:8000/#login",'Smart Identity (IBU)')
	reply = system_call(reply,"http://192.168.5.56:8002/#login",'Mewruk')
	reply = system_call(reply,"http://192.168.5.56:8001/#login",'Mitras Global')
	reply = system_call(reply,"http://192.168.5.56:8001/#login",'UAT')

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



#Daily check permission count and send mail
def permission_count():
	query = "SELECT * from `tabCustom DocPerm`"
	test= frappe.db.sql(query,as_dict=1)
	
	frappe.sendmail(
		recipients=["ravi.patel@mantratec.com","abhishek.jain@mantratec.com"],
		subject="Document Permission Count {}".format(len(test)),
		message="This is to track permission count"
	)

	return "Mail send for permission count"


#Weekly mail to check point
def weekly_check_checkpoints():

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




@frappe.whitelist()
def employee_remain_bank_account(allow_guest=True):
    # This method is call from cron every day to remain remain bank account list of employee.
    frappe.enqueue(employee_remain_bank_account_background, queue='long', timeout=10000)
    frappe.enqueue(employee_remain_email_id_background, queue='long', timeout=10000)
    
    return True

@frappe.whitelist()
def employee_remain_bank_account_background(**kwargs):
    
	query = "SELECT * from `tabEmployee` WHERE `status`='Active'"
	employee_list= frappe.db.sql(query,as_dict=1)
 
	query = "SELECT party,name,workflow_state from `tabBank Account` WHERE `party_type`='Employee' AND `disabled`=0 AND `workflow_state`='Approved'"
	bankaccount_list= frappe.db.sql(query,as_dict=1)
  
	query = "SELECT party,name,workflow_state from `tabBank Account` WHERE `party_type`='Employee' AND `disabled`=0 AND `workflow_state`!='Approved'"
	bankaccount_not_approve_list= frappe.db.sql(query,as_dict=1)
  
	account_not_found = []
	account_created_but_not_approve = []
	for employee in employee_list:
		account_found = False

		for account in bankaccount_list:
			if employee['name']==account['party']:
				account_found = True
				break

		account_created = False
		if not account_found:
			for account in bankaccount_not_approve_list:
				if employee['name']==account['party']:
					employee['workflow_state']=account['workflow_state']
					account_created = True
					break

			if account_created:
				account_created_but_not_approve.append(employee)
			else:
				account_not_found.append(employee)
 
	message = ""
	if len(account_not_found)>0:
		message = "{}<b>The list of employees whose bank accounts have been not created.<br><br>Total : {}</b>".format(message,len(account_not_found))
		message = '{}<br><br><table style="width: 100%;"><tbody><tr><td style="width: 50.0000%;"><strong>Employee Code</strong></td><td style="width: 50.0000%;"><strong>Employee Name</strong></td></tr>'.format(message)
		for employee in account_not_found:
			message = '{}<tr><td style="width: 50.0000%;"><a href="{}/app/employee/{}">{}</a></td><td style="width: 50.0000%;">{}</td></tr>'.format(message,site_base_url(),employee['name'],employee['name'],employee['employee_name'])
		message = '{}</tbody></table>'.format(message)
  
	if len(account_created_but_not_approve)>0:
		message = "{}<br><br><br><br>".format(message)
  
		message = "{}<b>The list of employees whose bank accounts have been disabled, denied approval .<br><br>Total : {}</b>".format(message,len(account_created_but_not_approve))
		message = '{}<br><br><table style="width: 100%;"><tbody><tr><td style="width: 33.0000%;"><strong>Employee Code</strong></td><td style="width: 33.0000%;"><strong>Status</strong></td><td style="width: 33.0000%;"><strong>Employee Name</strong></td></tr>'.format(message)
		for employee in account_created_but_not_approve:
			message = '{}<tr><td style="width: 33.0000%;"><a href="{}/app/employee/{}">{}</a></td><td style="width: 33.0000%;">{}</td><td style="width: 33.0000%;">{}</td></tr>'.format(message,site_base_url(),employee['name'],employee['name'],employee['workflow_state'],employee['employee_name'])
		message = '{}</tbody></table>'.format(message)
	
		# recipient_text = frappe.get_doc("ERP Settings").email_recipients_employee_bank_account_not_created
		# recipients = recipient_text.split(',')

		# if len(recipients)==0:
		# 	return "No email recipients is found."



	if len(account_not_found)>0 or len(account_created_but_not_approve)>0:
		# recipients=['ravi.patel@mantratec.com','anil.vadhel@mantratec.com']
		# recipients=['ravi.patel@mantratec.com']
		frappe.sendmail(
			recipients=employee_mail,
			subject="{} employees whose bank accounts have been disabled, denied approval, or not created".format(len(account_not_found)+len(account_created_but_not_approve)),
			message=message,
			now = True
		)
 
	return "Mail send for employee account not found data to respective users."

def employee_remain_email_id_background(**kwargs):
    
	query = "SELECT * from `tabEmployee` WHERE `status`='Active'"
	employee_list= frappe.db.sql(query,as_dict=1)
  
	account_not_found = []
	for employee in employee_list:
		if employee['prefered_email'] in [None,'',"None"]:
			account_not_found.append(employee)
 

	if len(account_not_found)>0:
		message = ""
		message = "{}<b>The list of employees whose prefered Email is not found. This email ID is use to send salary slip.<br><br>Total : {}</b>".format(message,len(account_not_found))
		message = '{}<br><br><table style="width: 100%;"><tbody><tr><td style="width: 50.0000%;"><strong>Employee Code</strong></td><td style="width: 50.0000%;"><strong>Employee Name</strong></td></tr>'.format(message)
	
		for employee in account_not_found:
			message = '{}<tr><td style="width: 50.0000%;"><a href="{}/app/employee/{}">{}</td><td style="width: 50.0000%;">{}</td></tr>'.format(message,site_base_url(),employee['name'],employee['name'],employee['employee_name'])

		message = '{}</tbody></table>'.format(message)	

		# recipients=['ravi.patel@mantratec.com']

		frappe.sendmail(
			recipients=employee_mail,
			subject="{} employees whose prefered Email is not found.".format(len(account_not_found)),
			message=message
		)
 
	return "Mail send for prefered Email not found to respective employee."


@frappe.whitelist(allow_guest=True)
def employee_names_validation_and_notify():
   
	try:
		name_regex = re.compile("^[A-Za-z\s]+$")
		invalid_employees = []

		query = "SELECT name,first_name,middle_name,last_name,employee_name FROM `tabEmployee` WHERE `status`='Active'"
		employees= frappe.db.sql(query,as_dict=1)

		for emp in employees:
			for field in ['first_name', 'middle_name', 'last_name','employee_name']:
				name = emp.get(field)
				if name and not name_regex.match(name):
					invalid_employees.append({
						"name": emp.name,
						"employee_name": emp.employee_name
					})
					break  # Skip checking other fields if one is invalid


		if invalid_employees:
			body = ""
			body = "{}<b>The following employees have invalid characters in their names:<br><br>Total : {}<br><br>No special charecter are allow in name</b>".format(body,len(invalid_employees))
			body = '{}<br><br><table style="width: 100%;"><tbody><tr><td style="width: 50.0000%;"><strong>Employee Code</strong></td><td style="width: 50.0000%;"><strong>Employee Name</strong></td></tr>'.format(body)
		
			for employee in invalid_employees:
				body = '{}<tr><td style="width: 50.0000%;"><a href="{}/app/employee/{}">{}</td><td style="width: 50.0000%;">{}</td></tr>'.format(body,site_base_url(),employee['name'],employee['name'],employee['employee_name'])

			body = '{}</tbody></table>'.format(body)
   
			# recipients=['ravi.patel@mantratec.com']
			frappe.sendmail(
				recipients=employee_mail,  # Replace with actual HR email
				subject="Invalid Employee Name(s) Detected",
				message=body,
			)
		return "Process done {}".format(len(invalid_employees))
	except Exception as e:
		frappe.sendmail(
			recipients=['ravi.patel@mantratec.com'],  # Replace with actual HR email
			subject="Error while checking employee name",
			message="{}<br>{}".format(str(e),str(traceback.format_exc())),
		)
  
@frappe.whitelist(allow_guest=True)
def check_last_backup_time_and_notify():
   try:
       backup_path = frappe.get_site_path("private", "backups")
       latest_time = None

       if not os.path.exists(backup_path):
           subject="Backup Alert: Folder Missing"
           message="<b>Backup folder not found at path:</b><br>{}".format(backup_path)
      
       # Find the latest modified file in the backup directory
       for file in os.listdir(backup_path):
           file_path = os.path.join(backup_path, file)
           if os.path.isfile(file_path):
               modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
               if not latest_time or modified_time > latest_time:
                   latest_time = modified_time

       if not latest_time:
           subject="Backup Alert: No Files Found"
           message="No backup files found in <b>{}</b>".format(backup_path)
      
       # Calculate the time difference
       current_time = datetime.now()
       diff = current_time - latest_time
       hours_since_backup = int(diff.total_seconds() // 3600)

       if diff > timedelta(hours=6):
           subject= f"Backup Alert: More than {hours_since_backup} Hour(s) Since Last Backup"
           message = f"""
               <b>Backup Alert:</b><br><br>
               Last backup was taken at <b>{latest_time.strftime('%Y-%m-%d %H:%M:%S')}</b><br>
               Time since last backup: <b>{hours_since_backup} hour(s)</b><br><br>
               Please ensure backup is running on schedule.
           """
       frappe.sendmail(
           recipients=["ravi.patel@mantratec.com"],  # Add relevant email
           subject= subject,
           message=message
       )

       return f"Backup alert sent."
      
   except Exception as e:
       frappe.sendmail(
           recipients=["ravi.patel@mantratec.com"],
           subject="Error: Could not check last backup time",
           message=f"""
               An error occurred while checking the last backup time:<br><br>
               <b>Error:</b> {str(e)}<br><br>
               <b>Traceback:</b><br>
               <pre>{frappe.get_traceback()}</pre>
           """
       )
       return "Error occurred. Notification sent."