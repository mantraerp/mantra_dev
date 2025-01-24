import frappe
from frappe import _
import traceback
import json
from mantra_dev.backend_code.globle import errorLog,errorLogExites,site_base_url



@frappe.whitelist()
def employee_remain_bank_account(allow_guest=True):
    #This method is call from cron every day to remain remain bank account list of employee.
    frappe.enqueue(employee_remain_bank_account_background, queue='long', timeout=10000)
    frappe.enqueue(employee_remain_email_id_background, queue='long', timeout=10000)
    
    return True

# @frappe.whitelist(allow_guest=True)
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
		recipients=['hrops@mantratec.com','anil.vadhel@mantratec.com','mukund.kotadia@mantratec.com','anurag@mantratec.com','ravi.patel@mantratec.com']
		# recipients=['ravi.patel@mantratec.com','anil.vadhel@mantratec.com']
		# recipients=['ravi.patel@mantratec.com']
		frappe.sendmail(
			recipients=recipients,
			subject="{} employees whose bank accounts have been disabled, denied approval, or not created".format(len(account_not_found)+len(account_created_but_not_approve)),
			message=message,
			now = True
		)
 
	return "Mail send for employee account not found data to respective users."


# @frappe.whitelist(allow_guest=True)
@frappe.whitelist()
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
	
		# recipient_text = frappe.get_doc("ERP Settings").email_recipients_employee_bank_account_not_created
		# recipients = recipient_text.split(',')

		# if len(recipients)==0:
		# 	return "No email recipients is found."

		recipients=['hrops@mantratec.com','anil.vadhel@mantratec.com','mukund.kotadia@mantratec.com','ravi.patel@mantratec.com']
		# recipients=['ravi.patel@mantratec.com']


		frappe.sendmail(
			recipients=recipients,
			subject="{} employees whose prefered Email is not found.".format(len(account_not_found)),
			message=message
		)
 
	return "Mail send for prefered Email not found to respective employee."




#To create entry in erro log
@frappe.whitelist(allow_guest=True)
def minop_hook(**kwargs):

	parameters=frappe._dict(kwargs) 
	parameters['status_code']=200
	parameters['sucessfull']=True
	return parameters
		# query = "SELECT * from `tabError Log` WHERE error='{}' AND method='{}'".format(error,title)
		# test= frappe.db.sql(query,as_dict=1)