from __future__ import unicode_literals
import frappe
from frappe import _
import traceback
# import frappe
from frappe.utils import today

# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.salary_slip.not_sent_slip
# def not_sent_slip(payroll_no):
# @frappe.whitelist(allow_guest=True)
def not_sent_slip():
	doc = frappe.get_all("Salary Slip", filters={
    'status': 'Submitted',
	'payroll_entry':"HR-PRUN-2025-00026"
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
	# 	for j in doc:
	# 		if i[0] == j[0]:
	# 			x.append(i[0])
	# 		else:
	# 			pass
	x = []
	for i in sal_slip_sub:
		if i in email_q:
			pass
		else:
			x.append(i)
	return x
	return f"Email :{len(email_q)}, Payroll: {len(sal_slip_sub)}"
	# return f"email: {len(email_queue)},payroll: {len(doc)}"

# Sal Slip/MN001700/00002 = email not there
# Sal Slip/MN001699/00001 = email not there
# Sal Slip/MN001698/00002 = email not there
# Sal Slip/MN001697/00002 = email not there
# Sal Slip/MN001696/00002 = email not there
# Sal Slip/MN001655/00001 = email not there



# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.salary_slip.get_payroll?payroll_no=HR-PRUN-2025-00026

# frappe.db.get_list('Task',
#     filters={
#         'status': 'Open'
#     },
#     fields=['subject', 'date'],
#     order_by='date desc',
#     start=10,
#     page_length=20,
#     as_list=True
# )
# @frappe.whitelist(allow_guest=True)
# @frappe.whitelist()
def get_payroll(payroll_no):
	doc = frappe.get_all("Salary Slip", filters={
    'status': 'Submitted',
	'payroll_entry':payroll_no
    },
    fields=['name'],
    as_list=True)
	for i in doc:
		# if str(i[0]) == "Sal Slip/MN001682/00003":
		email_salary_slip(i[0])
			# frappe.enqueue(email_salary_slip,queue='long',job_name="Salary slip email {}".format(str(i[0])),timeout=100000,salary_slip_no=str(i[0]))
	return doc

# @frappe.whitelist(allow_guest=True)
# def middle_ware(sal_no):
# 	frappe.enqueue(email_salary_slip,queue='long',job_name="Salary slip email {}".format(str(sal_no)),timeout=100000,salary_slip_no=str(sal_no))
# 	# pass



# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.salary_slip.email_salary_slip?salary_slip_no=Sal Slip/MN001682/00003
# @frappe.whitelist()
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
		

		employee_code = salary_slip_detail[0]['employee']


		receiver = frappe.db.get_value("Employee", employee_code, "prefered_email")
		payroll_settings = frappe.get_single("Payroll Settings")
		message = "Please see attachment"
		password = None
		if payroll_settings.encrypt_salary_slips_in_emails:
			password = generate_password_for_pdf(payroll_settings.password_policy, employee_code)
			message += """<br>Note: Your salary slip is password protected,
				the password to unlock the PDF is of the format {0}. """.format(
				payroll_settings.password_policy
			)



		if receiver:
			# email_args = {
			# 	"recipients": [receiver],
			# 	"message": _(message),
			# 	"subject": "Salary Slip - from {0} to {1}".format(salary_slip_detail[0]['start_date'], salary_slip_detail[0]['end_date']),
			# 	"attachments": [
			# 		frappe.attach_print('Salary Slip', salary_slip_no, file_name=salary_slip_no, password=password)
			# 	],
			# 	"reference_doctype": 'Salary Slip',
			# 	"reference_name": salary_slip_no,
			# }
			# frappe.sendmail(**email_args)




			document = frappe.get_doc("Salary Slip",salary_slip_no)
			doc_args = document.as_dict()


			# if data.get("contact"):
			# 	contact = frappe.get_doc("Contact", data.get("contact"))
			# 	doc_args["contact"] = contact.as_dict()

# Salary Slip for {% set month= frappe.utils.formatdate(start_date, "MMMM YYYY") %}{{month}}
			doc_args.update(
				{
					"start_date": document.start_date,
					"employee_name": document.employee_name,
				}
			)


			# if not self.email_template:
			# 	return


			email_template = frappe.get_doc("Email Template", "Salary Slip")
			message = frappe.render_template(email_template.response_, doc_args)
			subject = frappe.render_template(email_template.subject, doc_args)
			# sender = frappe.session.user not in STANDARD_USERS and frappe.session.user or None






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
		# if salary_slip_detail[0]['docstatus'] in [0,2]:	
			# frappe.msgprint(_("{0}: Employee email not found, hence email not sent").format(employee_code))
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
		frappe.msgprint(str(error))
		return "Error send in mail"


def generate_password_for_pdf(policy_template, employee):
	employee = frappe.get_doc("Employee", employee)
	return policy_template.format(**employee.as_dict())







# frappe.sendmail(
# 				recipients = [receiver],
# 				message = _(message),
# 				subject= "Salary Slip - from {0} to {1}".format(salary_slip_detail[0]['start_date'], salary_slip_detail[0]['end_date']),
# 				attachments= [
# 					frappe.attach_print('Salary Slip', salary_slip_no, file_name=salary_slip_no, password=password)
# 				],
# 				reference_doctype= 'Salary Slip',
# 				reference_name= salary_slip_no,
# 				now = True
# 			)