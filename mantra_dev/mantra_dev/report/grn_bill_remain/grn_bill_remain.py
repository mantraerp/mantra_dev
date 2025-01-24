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
							"{}".format(row['total_qty']),
							"100%",

							row['status'],
							row['owner'],
							get_purchase_order_from_receipt(row['name']),
							row['supplier'],
							row['supplier_name'],

						])
					else:
						bill_created = check_created_status(row['name'],filters)
						total_remaining = row['total_qty']-bill_created

						if not filters.get("remove_created_bill"):
      
							data.append([
								row['name'],
								row['posting_date'],

								row['total_qty'],
								"{}".format(bill_created),

								"{}".format(total_remaining),
								"{}%".format(dividation_value(row['total_qty'],bill_created)),

								row['status'],
								row['owner'],
								get_purchase_order_from_receipt(row['name']),
								row['supplier'],
								row['supplier_name'],
							])

	except Exception as e:
		error = '{} - {}'.format(str(e),str(traceback.format_exc()))
		frappe.msgprint(str(error))
		
	return columns, data

def get_purchase_order_from_receipt(receipt_name):
    
	query = """SELECT owner FROM `tabPurchase Order` WHERE `name` in (SELECT pri.purchase_order AS purchase_order FROM `tabPurchase Receipt Item` pri WHERE pri.purchase_order IS NOT NULL AND pri.parent = '"""+receipt_name+"""')"""
	data_raw = frappe.db.sql(query,as_dict=1)
	
	if len(data_raw) != 0:
		return data_raw[0]['owner']

	return ""


def dividation_value(v1,v2):

	if v1==0:
		return 0
	
	if v2==0:
		return 0

	return int((((v1-v2)*100)/v2))



def check_created_status(pr_no,filters):

	query = """SELECT pii.qty,pii.item_code,pii.name as docname,pi.name,pii.amount,pi.grand_total,pi.owner FROM `tabPurchase Invoice Item` AS pii INNER JOIN `tabPurchase Invoice` AS pi ON pi.name=pii.parent WHERE pi.status NOT IN ('Cancelled') AND pi.workflow_state NOT IN ('Rejected') AND pii.purchase_receipt='"""+str(pr_no)+"""'"""
	data_raw = frappe.db.sql(query,as_dict=1)

	nameProcess = []
	amount = 0.0

	for index, row in enumerate(data_raw):
		if filters.get("remove_service_items"):
			if not frappe.db.get_value("Item", row['item_code'], "custom_is_service_item"):
				if row['docname'] not in nameProcess:
					nameProcess.append(row['docname'])
					amount += row['qty']
		else:
			if row['docname'] not in nameProcess:
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

	sorting = "ASC"
	if filters.get("new_to_old"):
		sorting = "DESC"
	# yearDetail = frappe.db.sql("""SELECT * FROM `tabPurchase Receipt` WHERE name=%s""",year,as_dict=1)
	# return frappe.db.sql("""SELECT * FROM `tabPurchase Receipt` WHERE `status` NOT IN ('Completed','Cancelled','Closed') AND `is_return`=0""",as_dict=1)
	query = "SELECT * FROM `tabPurchase Receipt` WHERE `status` IN ('To Bill') AND `is_return`=0 ORDER BY `posting_date` {}".format(sorting)
	return frappe.db.sql(query,as_dict=1)


def get_columns(filters):
	

	columns= []
	columns.append({'fieldname':'pr','label':"Purchase Receipt",'fieldtype':'Link',"options":"Purchase Receipt",'align':'left','width':225})
	columns.append({'fieldname':'pr_date','label':"Date",'fieldtype':'data','align':'left','width':120})

	
	columns.append({'fieldname':'pr_total','label':"Total",'fieldtype':'data','align':'left','width':90})
	columns.append({'fieldname':'pr_bill_create_remain','label':"Bill Create",'fieldtype':'data','align':'left','width':90})

	columns.append({'fieldname':'pr_create_remain','label':"Remain",'fieldtype':'data','align':'left','width':90})
	columns.append({'fieldname':'pr_create_remain_per','label':"Remain %",'fieldtype':'data','align':'left','width':90})

	# columns.append({'fieldname':'pr_bill_completed','label':"Bill Completed",'fieldtype':'data','align':'left','width':100})

	columns.append({'fieldname':'pr_status','label':"Status",'fieldtype':'data','align':'left','width':100})
	columns.append({'fieldname':'pr_owner','label':"PR Created By",'fieldtype':'data','align':'left','width':140})
	columns.append({'fieldname':'po_owner','label':"PO Created By",'fieldtype':'data','align':'left','width':140})

	columns.append({'fieldname':'pr_supplier','label':"Supplier",'fieldtype':'data','align':'left','width':100})
	columns.append({'fieldname':'pr_supplier_name','label':"Supplier Name",'fieldtype':'data','align':'left','width':150})

	# columns.append({'fieldname':'party','label':"Party",'fieldtype':'data','align':'left','width':270})
	# columns.append({'fieldname':'amount','label':"Amount",'fieldtype':'data','align':'right','width':150})
	# columns.append({'fieldname':'s_c_type','label':"Supplier Group/Customer Type",'fieldtype':'data','align':'right','width':270})

	return columns