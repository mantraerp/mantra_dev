import frappe # type: ignore
import traceback


@frappe.whitelist()
def party_detail(party,party_type):

	reply={}
	reply['message']="Account not found."
	reply['status_code']=200
	reply['data']=[]
	reply['email']=""

	try:
		directory_sql = "SELECT * FROM `tabBank Account` WHERE `workflow_state`='Approved' AND `is_company_account`=0 AND `custom_beneficiary_file_uploaded`=1 AND `is_default`=1 AND `disabled`=0 AND `party`='{}'".format(party)
		directory_list = frappe.db.sql(directory_sql, as_dict=True)
		reply['data']=directory_list

		if party_type=="Supplier":
			query_supplier = "SELECT email_id FROM `tabSupplier` WHERE `name`='{}'".format(party)
			list_supplier = frappe.db.sql(query_supplier, as_dict=True)
			if len(list_supplier)!=0:
				if list_supplier[0]['email_id'] not in ['',None,'null']:
					reply['email']=list_supplier[0]['email_id']

		if party_type=="Customer":
			query_customer = "SELECT email_id FROM `tabCustomer` WHERE `name`='{}'".format(party)
			list_customer = frappe.db.sql(query_customer, as_dict=True)
			if len(list_customer)!=0:
				if list_customer[0]['email_id'] not in ['',None,'null']:
					reply['email']=list_customer[0]['email_id']

		if party_type=="Employee":
			query_employee = "SELECT prefered_email FROM `tabEmployee` WHERE `name`='{}'".format(party)
			list_employee = frappe.db.sql(query_employee, as_dict=True)
			if len(list_employee)!=0:
				if list_employee[0]['prefered_email'] not in ['',None,'null']:
					reply['email']=list_employee[0]['prefered_email']

		if len(directory_list)==0:
			reply['message']="No account found."
			reply['status_code']=500

	except Exception as e:
		reply['message']=str(e)
		reply['status_code']=500
		frappe.log_error("Bank account detail fetch error",str(traceback.format_exc()))

	return reply


@frappe.whitelist()
def company_bank_account_detail(mode_of_payment):
    #Call from payment_entry.js
    #Get data from payment entry (mode_of_payment). check into Mode of payment list.
    #If data found then return company bank account
    #If not found then send blank
    #If require to have Bank account read permission

	try:
		if mode_of_payment:
			doc1 = frappe.get_doc("Mode of Payment",mode_of_payment)
			if doc1.accounts:
				for row in doc1.accounts:
					if row.default_account:
						set_acc = frappe.db.get_list('Bank Account',
							filters={
								'is_company_account':1
							},
							or_filters=[
								['account', '=', row.default_account],
								['name', '=', row.default_account]
							],
							fields=['name', 'account'],
							as_list=True
						)
						if set_acc:
							for i in set_acc:
								return i[0]
						else:
							return ""
					else:
						return ""
			else:
				return ""
	except Exception as e:
		frappe.log_error("Payment entry page error","Mode of payment issue {}<br>{}".format(str(e),str(traceback.format_exc())))
		return ""