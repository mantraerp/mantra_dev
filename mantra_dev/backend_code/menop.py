import frappe
from frappe import _
import traceback
import json




@frappe.whitelist()
def employee_remain_bank_account():
    #This method is call from cron every day to remain remain bank account list of employee.
    frappe.enqueue(employee_remain_bank_account_background, queue='long', timeout=10000)
    return True

@frappe.whitelist()
def employee_remain_bank_account_background(**kwargs):
    
	query = "SELECT * from `tabEmployee` WHERE `status`='Active'"
	employee_list= frappe.db.sql(query,as_dict=1)
 
	query = "SELECT party,name from `tabBank Account` WHERE `party_type`='Employee' AND `is_default`=1 AND `disabled`=0 AND `workflow_state`='Approved'"
	bankaccount_list= frappe.db.sql(query,as_dict=1)
  
	account_not_found = []
	for employee in employee_list:
		account_found = False
		for account in bankaccount_list:
			if employee['name']==account['party']:
				account_found = True;
				break

		if not account_found:
			account_not_found.append(employee)
 

	if len(account_not_found)>0:
		message = ""
		message = "{}<b>The list of employees whose bank accounts have been disabled, denied approval, or not created.<br><br>Total : {}</b>".format(message,len(account_not_found))
		
		message = '{}<br><br><table style="width: 100%;"><tbody><tr><td style="width: 50.0000%;"><strong>Employee Code</strong></td><td style="width: 50.0000%;"><strong>Employee Name</strong></td></tr>'.format(message)
	
		for employee in account_not_found:

			message = '{}<tr><td style="width: 50.0000%;">{}</td><td style="width: 50.0000%;">{}</td></tr>'.format(message,employee['name'],employee['employee_name'])


		message = '{}</tbody></table>'.format(message)
	
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="{} employees whose bank accounts have been disabled, denied approval, or not created".format(len(account_not_found)),
			message=message
		)
 
	return "Mail send for employee account not found data."





#To create entry in erro log
@frappe.whitelist(allow_guest=True)
def minop_hook(**kwargs):
# def minop_hook(): 
    # return "ravi"  
	parameters=frappe._dict(kwargs)
	return parameters
		# query = "SELECT * from `tabError Log` WHERE error='{}' AND method='{}'".format(error,title)
		# test= frappe.db.sql(query,as_dict=1)