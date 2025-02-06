import frappe # type: ignore
from frappe import _ # type: ignore
from mantra_dev.backend_code.globle import errorLog # type: ignore

@frappe.whitelist(allow_guest=True)
def sales_order_auto_close():

	reply={}
	reply['message']=""


	query = "SELECT soi.name,soi.item_code,soi.qty,so.name as so_name FROM `tabSales Order Item` soi JOIN `tabItem` i ON soi.item_code=i.name JOIN `tabSales Order` so ON soi.parent = so.name WHERE i.custom_is_service_item=1 AND so.status NOT IN ('Completed','Closed','Cancelled','Draft','To Bill')"
	sales_order_item = frappe.db.sql(query, as_dict=True)

	reply['data']=sales_order_item
	reply['data_length']=len(sales_order_item)
	# return reply
	
	for index, record in enumerate(sales_order_item):
		# if index<10:
		# if record['so_name'] not in ['SO/23-24/03/0033642','SO/23-24/03/0033783','SO/24-25/06/0006691']:
		# if record['so_name'] in ['SO/24-25/07/0004572']:
		# errorLog("Sales order",record['so_name'])
		frappe.enqueue(sales_order_auto_close_update_delivered_qty,queue='long',job_name="So Process",timeout=100000,record=record)

	return reply


@frappe.whitelist(allow_guest=True)
def sales_order_auto_close_update_delivered_qty_value(so_no):

	doc = frappe.get_doc("Sales Order", so_no)
	# return doc
	query = """SELECT 
				so.name AS sales_order,
				si.name AS sales_invoice,
				si.posting_date,
				si.customer,
				si.grand_total AS invoiced_amount
			FROM 
				`tabSales Invoice` si
			JOIN 
				`tabSales Invoice Item` sii ON si.name = sii.parent
			JOIN 
				`tabSales Order` so ON sii.sales_order = so.name
			WHERE 
				si.docstatus = 1
				AND so.name = '{}'
			GROUP BY 
				si.name
			ORDER BY 
				si.posting_date""".format(so_no)
	sales_order_item_update = frappe.db.sql(query, as_dict=True)
 
	si_process = []
	total_invoice_amount = 0
	for siprocess in sales_order_item_update:
		if siprocess['sales_invoice'] not in si_process:
			si_process.append(siprocess['sales_invoice'])
			total_invoice_amount += float(siprocess['invoiced_amount'])
 
	return round(total_invoice_amount,2)

@frappe.whitelist(allow_guest=True)
def sales_order_auto_close_update_delivered_qty(record):
    
	try:
		if frappe.db.exists("Sales Order", record['so_name']):
			query = "UPDATE `tabSales Order Item` SET `delivered_qty`={} WHERE `name`='{}' AND `item_code`='{}'".format(record['qty'],record['name'],record['item_code'])
			sales_order_item_update = frappe.db.sql(query, as_dict=False)
	
			doc = frappe.get_doc("Sales Order", record['so_name'])
			new_delivered_qty = 0
			for item in doc.items:
				new_delivered_qty = new_delivered_qty + item.delivered_qty					

			frappe.db.set_value("Sales Order",doc.name,"per_delivered",(new_delivered_qty / doc.total_qty) * 100)

			doc = frappe.get_doc("Sales Order", record['so_name'])
			if doc.grand_total==0:
				doc.update_status("Closed")

			# errorLog("Sales order",'Sart matching')
			# errorLog("Sales order",round(doc.per_billed, 2))
			# errorLog("Sales order",round(doc.per_billed, 2))
			if doc.per_billed == 100 and doc.per_billed==100:
				# errorLog("Sales order",'match with 100')
				if doc.grand_total == sales_order_auto_close_update_delivered_qty_value(record['so_name']):
					doc.update_status("Completed")
				else:
					errorLog("Sales order- amount and delivery is 100 but grand total not match",record['so_name'])

					# errorLog("Sales order",'completed')

	except Exception as e:
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Sales order auto close : {}".format(record['so_name']),
			message="{}<br>{}".format(str(record),str(e))
		)
	return True