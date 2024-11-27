# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
import traceback


def execute(filters=None):
	columns, data = [], []


	try:
		columns = get_columns(filters)


		data_raw = getProcessData(filters)
		nameProcess = []

		for index, row in enumerate(data_raw):
			if row['name'] not in nameProcess:
				nameProcess.append(row['name'])

				if row['docstatus']!=2:
					if row['custom_processed']==0:
						data.append([
							row['name'],
							row['posting_date'],

							"{}".format(row['total_qty']),
							"0",
							"0",
							"100%",

							row['status'],
							row['supplier'],
							row['supplier_name'],

						])
					else:
						bill_created = check_created_status(row['name'],row['grand_total'])
						data.append([
							row['name'],
							row['posting_date'],

							row['total_qty'],
							"{}".format(bill_created),

							"{}".format(row['total_qty']-bill_created),
							"{}%".format(dividation_value(row['total_qty'],bill_created)),
							

							row['status'],
							row['supplier'],
							row['supplier_name'],

						])

	except Exception as e:
		error = '{} - {}'.format(str(e),str(traceback.format_exc()))
		frappe.msgprint(str(error))
		
	return columns, data

def dividation_value(v1,v2):

	if v1==0:
		return 0
	
	if v2==0:
		return 0

	return round((((v1-v2)*100)/v2),2),



def check_created_status(pr_no,grand_total):

	query = """SELECT pii.qty,pii.name as docname,pi.name,pii.amount,pi.grand_total FROM `tabPurchase Invoice Item` AS pii INNER JOIN `tabPurchase Invoice` AS pi ON pi.name=pii.parent WHERE pi.status NOT IN ('Cancelled') AND pii.purchase_receipt='"""+str(pr_no)+"""'"""
	data_raw = frappe.db.sql(query,as_dict=1)

	nameProcess = []
	amount = 0.0

	for index, row in enumerate(data_raw):
		# if pr_no=="PR-24-00049":
		# 	frappe.msgprint(str(row['docname']))
		if row['docname'] not in nameProcess:
			# if pr_no=="PR-24-00049":
			# 	frappe.msgprint(str(row['amount']))

			nameProcess.append(row['docname'])
			amount += row['qty']

	return amount



def check_created_status_amount(pr_no,grand_total):

	query = """SELECT pii.name as docname,pi.name,pii.amount,pi.grand_total FROM `tabPurchase Invoice Item` AS pii INNER JOIN `tabPurchase Invoice` AS pi ON pi.name=pii.parent WHERE pi.status NOT IN ('Cancelled') AND pii.purchase_receipt='"""+str(pr_no)+"""'"""
	data_raw = frappe.db.sql(query,as_dict=1)

	nameProcess = []
	amount = 0.0

	for index, row in enumerate(data_raw):
		# if pr_no=="PR-24-00049":
		# 	frappe.msgprint(str(row['docname']))
		if row['docname'] not in nameProcess:
			# if pr_no=="PR-24-00049":
			# 	frappe.msgprint(str(row['amount']))

			nameProcess.append(row['docname'])
			amount += row['amount']


	# if pr_no=="PR-24-00049":
	# # 	frappe.msgprint(str(query))

	# 	frappe.msgprint(str(len(data_raw)))

	# 	frappe.msgprint(str(grand_total))
	# 	frappe.msgprint(str(amount))

	if amount==0:
		return 0
	
	if grand_total==0:
		return 0

	return (amount*100)/grand_total




# Purchase Receipt

def getProcessData(filters):

	# yearDetail = frappe.db.sql("""SELECT * FROM `tabPurchase Receipt` WHERE name=%s""",year,as_dict=1)
	return frappe.db.sql("""SELECT * FROM `tabPurchase Receipt` WHERE `status` NOT IN ('Completed','Cancelled','Closed') AND `is_return`=0""",as_dict=1)


def get_columns(filters):
	

	columns= []
	columns.append({'fieldname':'pr','label':"Purchase Receipt",'fieldtype':'Link',"options":"Purchase Receipt",'align':'left','width':230})
	columns.append({'fieldname':'pr_date','label':"Date",'fieldtype':'data','align':'left','width':120})

	
	columns.append({'fieldname':'pr_total','label':"Total",'fieldtype':'data','align':'left','width':100})
	columns.append({'fieldname':'pr__bill_create_remain','label':"Bill Create",'fieldtype':'data','align':'left','width':100})

	columns.append({'fieldname':'pr_create_remain','label':"Remain",'fieldtype':'data','align':'left','width':100})
	columns.append({'fieldname':'pr_create_remain_per','label':"Remain %",'fieldtype':'data','align':'left','width':100})

	# columns.append({'fieldname':'pr_bill_completed','label':"Bill Completed",'fieldtype':'data','align':'left','width':100})

	columns.append({'fieldname':'pr_status','label':"Status",'fieldtype':'data','align':'left','width':100})
	columns.append({'fieldname':'pr_supplier','label':"Supplier",'fieldtype':'data','align':'left','width':100})
	columns.append({'fieldname':'pr_supplier_name','label':"Supplier Name",'fieldtype':'data','align':'left','width':150})

	# columns.append({'fieldname':'party','label':"Party",'fieldtype':'data','align':'left','width':270})
	# columns.append({'fieldname':'amount','label':"Amount",'fieldtype':'data','align':'right','width':150})
	# columns.append({'fieldname':'s_c_type','label':"Supplier Group/Customer Type",'fieldtype':'data','align':'right','width':270})

	return columns