from __future__ import unicode_literals
import frappe
from frappe import _
import traceback
# import frappe
from frappe.utils import today
import requests

@frappe.whitelist(allow_guest=True)
# @frappe.whitelist()
def email_payroll_salary_slip(payroll_no):
    
	reply={}
	reply['message']=""
	reply['status_code']=500
 
	document = frappe.get_doc("Payroll Entry",payroll_no)
	if document.status!="Submitted":
		reply['message']="Payroll entry is not submitted."
		return reply
 

	salary_slip_list = frappe.get_all("Salary Slip", filters={
		'status': 'Submitted',
  		'custom_email_send':False,
		'payroll_entry':payroll_no
    }, fields=['name','status'])
  
	submitted = []
	for salary_slip in salary_slip_list:
		if salary_slip['status']=="Submitted":
			submitted.append(salary_slip)

	if len(salary_slip_list)==0:
		reply['message']="No submitted salary slip is found."
		return reply
	else:
		if len(submitted)==0:
			reply['message']="No submitted salary slip is found."
			return reply
      
		reply['status_code']=200
  
		query = "SELECT e.name FROM `tabEmployee` e JOIN `tabSalary Slip` ss ON e.name = ss.employee WHERE ss.payroll_entry = '{}' AND (e.prefered_email='' OR e.prefered_email IS NULL)".format(payroll_no)
		employee_list_without_email = frappe.db.sql(query, as_dict=True)
		message_without_email = ""
		for emp in employee_list_without_email:
			message_without_email="{}<br>{}".format(message_without_email,emp["name"])
	
  
		if len(submitted)!=len(salary_slip_list):

			reply['message']="Total {} salary slip found from that {} are submitted. Do you want to send mail to submitted salary slip ?<br><br><br>Employee list without email ID. Below employee will not get email of salary slip. <br>{}".format(len(salary_slip_list),len(submitted),message_without_email)
			return reply

		reply['message']="Total {} salary slip. Do you want to send mail ?<br><br><br>Employee list without email ID. Below employee will not get email of salary slip. <br>{}".format(len(salary_slip_list),message_without_email)
		return reply


@frappe.whitelist()
def email_payroll_salary_slip_back(payroll_no):
    
	reply={}
	reply['message']=""
	reply['status_code']=500

	salary_slip_list = frappe.get_all("Salary Slip", filters={
		'status': 'Submitted',
		'custom_email_send':False,
		'payroll_entry':payroll_no
    }, fields=['name'],as_list=True)
 

	for i in salary_slip_list:
		email_salary_slip(i[0])
	
	return reply


@frappe.whitelist(allow_guest=True)
def salary_slip_date_range(employee_id,from_date,to_date):
    
	reply={}
	reply['message']=""
	reply['status_code']=500
 
	salary_slip_list = frappe.get_all(
		"Salary Slip",
		filters={
			"employee": employee_id,
			"start_date": [">=", from_date],
			"end_date": ["<=", to_date],
			"docstatus": 1  # Ensure only submitted salary slips
		},
		fields=['name','status']
	)

	submitted = []
	for salary_slip in salary_slip_list:
		if salary_slip['status']=="Submitted":
			submitted.append(salary_slip)

	if len(salary_slip_list)==0:
		reply['message']="No submitted salary slip is found."
		return reply
	else:
		if len(submitted)==0:
			reply['message']="No submitted salary slip is found."
			return reply
		
		reply['status_code']=200

		query = "SELECT name FROM `tabEmployee` WHERE `name` = '{}' AND (`prefered_email`='' OR `prefered_email` IS NULL)".format(employee_id)
		employee_list_without_email = frappe.db.sql(query, as_dict=True)
		if len(employee_list_without_email)!=0:
			reply['message']="Prefered email address is not found."
			return reply


		reply['message']="Total {} salary slip found. Do you want to send mail to submitted salary slip ?".format(len(salary_slip_list))
		return reply


@frappe.whitelist()
def salary_slip_date_range_back(employee_id,from_date,to_date):
    
	reply={}
	reply['message']=""
	reply['status_code']=500

	salary_slip_list = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": employee_id,
            "start_date": [">=", from_date],
            "end_date": ["<=", to_date],
            "docstatus": 1  # Ensure only submitted salary slips
        },
        fields=['name'],as_list=True
    )
 

	for i in salary_slip_list:
		email_salary_slip(i[0])
	
	return reply


@frappe.whitelist()
# @frappe.whitelist(allow_guest=True)
def email_salary_slip(salary_slip_no):

	try:
		query = "SELECT * FROM `tabSalary Slip` WHERE `name`='{}'".format(salary_slip_no)
		salary_slip_detail = frappe.db.sql(query,as_dict=1)

		if len(salary_slip_detail)==0:
			frappe.sendmail(
				recipients = ['ravi.patel@mantratec.com'],
				subject = "Salary slip not found error: {}".format(salary_slip_no),
				content = "Salary slip not found error",
				now = True
			)
			return "Salary slip not found"

		if salary_slip_detail[0]['employee'] in ['',None,'None']:
			frappe.sendmail(
				recipients = ['ravi.patel@mantratec.com'],
				subject = "Salary slip Employee error: {}".format(salary_slip_no),
				content = "Employee code not found",
				now = True
			)
			return "Employee code not found"
		
		if salary_slip_detail[0]['docstatus'] in [0,2]:	
			frappe.sendmail(
				recipients = ['ravi.patel@mantratec.com'],
				subject = "Salary slip docstatus error: {}".format(salary_slip_no),
				content = "docstatus error",
				now = True
			)
			return "docstatus error"
		
  
		if salary_slip_detail[0]['custom_email_send'] in [1,True]:
			return "Salary slip is already send"


		employee_code = salary_slip_detail[0]['employee']


		receiver = frappe.db.get_value("Employee", employee_code, "prefered_email")
		payroll_settings = frappe.get_single("Payroll Settings")
		message = "Please see attachment" #if email templete is not set
		
		password = None
		if payroll_settings.encrypt_salary_slips_in_emails:
			password = generate_password_for_pdf(payroll_settings.password_policy, employee_code)
			message += """<br>Note: Your salary slip is password protected,
				the password to unlock the PDF is of the format {0}. """.format(
				payroll_settings.password_policy
			)

		if receiver:

			document = frappe.get_doc("Salary Slip",salary_slip_no)
			doc_args = document.as_dict()
			doc_args.update(
				{
					"start_date": document.start_date,
					"employee_name": document.employee_name,
				}
			)


			subject = "Salary slip {}".format(salary_slip_no) #if email templete is not set
			if payroll_settings.email_template not in [None,"","None"," "]:
				email_template = frappe.get_doc("Email Template", "Salary Slip")
				message = frappe.render_template(email_template.response_, doc_args)
				subject = frappe.render_template(email_template.subject, doc_args)



			frappe.db.set_value("Salary Slip", salary_slip_no, "custom_email_send", 1)
			frappe.sendmail(
				recipients = [receiver],
				message = message,
				subject= subject,
				attachments= [
					frappe.attach_print('Salary Slip', salary_slip_no, file_name=salary_slip_no, password=password)
				],
				reference_doctype= 'Salary Slip',
				reference_name= salary_slip_no,
				now = True
			)

		else:
			frappe.sendmail(
				recipients = ['ravi.patel@mantratec.com'],
				subject = "Employee email not found, hence email not sent: {}".format(salary_slip_no),
				content = "Employee email not found, hence email not sent",
				now = True
			)
			return "Employee email not found, hence email not sent"

		return "Email send"

	except Exception as e:
		error = '{} - {}'.format(str(e),str(traceback.format_exc()))
		frappe.sendmail(
			recipients = ['ravi.patel@mantratec.com'],
			subject = "Salary slip mail error: {}".format(salary_slip_no),
			content = error,
			now = True
		)
		return "Error send in mail"


def generate_password_for_pdf(policy_template, employee):
	employee = frappe.get_doc("Employee", employee)
	return policy_template.format(**employee.as_dict())





#######################  UTILITY  ######################################
@frappe.whitelist()
def create_bank_account(account_name, bank_name, account_type, party_type, party, custom_branch_location, bank_account_no,custom_ifsc):
	reply={}
	reply['message']=""
	reply['status_code']=500
	try:
     
		query = "SELECT * FROM `tabBank Account` WHERE `party_type`='{}' AND `party`='{}' AND `bank_account_no`='{}' AND `workflow_state` in ('Approved','Pending')".format(party_type,party,bank_account_no)
		bank_account_list = frappe.db.sql(query,as_dict=1)
		if len(bank_account_list)!=0:
			reply['message']="Same bank account with {} is found. If need to create new then cancelled previous created bank account.".format(bank_account_list[0]['workflow_state'])
			reply['status_code']=500
			return reply
     
     
		# Create a new Bank Account record
		bank_account = frappe.get_doc({
			"doctype": "Bank Account",
			"account_name": account_name,
			"bank": bank_name,
			"account_type": account_type,
			"party_type":party_type,
			"party":party,
			"custom_branch_location":custom_branch_location,
			"bank_account_no":bank_account_no,
			"custom_ifsc":custom_ifsc
		})
		# Insert the document into the database
		bank_account.insert()
		# frappe.db.commit()  # Commit changes to the database
		reply['message']=f"Bank Account '{account_name}' created successfully."
		reply['status_code']=200
		return reply
	except frappe.ValidationError as e:
		reply['message']=f"Validation Error: {str(e)}"
		reply['status_code']=500
	except Exception as e:
		error = '{} <br><br> {}'.format(str(e),str(traceback.format_exc()))
		reply['message']=error
		reply['status_code']=500
  
	return reply

@frappe.whitelist(allow_guest=True)
def branch_name_using_ifsc(ifsc):
    
	branch_name = ""
	
	try:
		url = "https://ifsc.razorpay.com/{}".format(ifsc)
		response = requests.get(url)
		if response.status_code == 200:
			branch_name = response.json()['BRANCH']
	except Exception as e:
		branch_name = ""
	return branch_name


#To check email is send or not
# @frappe.whitelist(allow_guest=True)
def not_sent_slip(payroll_no):
    
	doc = frappe.get_all("Salary Slip", filters={
		'status': 'Submitted',
		'custom_email_send':False,
		'payroll_entry':payroll_no
    },
    fields=['name'],
    as_list=True)

	email_queue = frappe.get_all("Email Queue", filters={
		'status': 'Sent',
		'reference_doctype':'Salary Slip',
		'creation': ('>=', today())
    },
    fields=['reference_name'],
    as_list=True)
	email_q = []
	sal_slip_sub = []
	for i in email_queue:
		email_q.append(i[0])
	for i in doc:
		sal_slip_sub.append(i[0])

	x = []
	for i in sal_slip_sub:
		if i in email_q:
			pass
		else:
			x.append(i)
	return x