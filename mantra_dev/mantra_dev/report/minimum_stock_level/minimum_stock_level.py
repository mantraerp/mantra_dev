# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

# import frappe


import frappe
import traceback

def execute(filters=None):
	columns, data = [], []


	try:
		columns = get_columns(filters)

		data_raw = getProcessData(filters)

		for index, row in enumerate(data_raw):

			safty_stock = row['safety_stock']
			if safty_stock in [None,""]:
				safty_stock = 0
			current_stock = get_latest_stock_qty(row['item_code'])
			if current_stock in [None,""]:
				current_stock = 0

			if safty_stock>current_stock:
				data.append([
					row['item_code'],
					row['item_name'],

					safty_stock,
					current_stock,
					"Yes" if safty_stock>current_stock else "No"
				])

	except Exception as e:
		error = '{} - {}'.format(str(e),str(traceback.format_exc()))
		frappe.msgprint(str(error))
		
	return columns, data


def get_latest_stock_qty(item_code):
	values, condition = [item_code], ""
	actual_qty = frappe.db.sql(
		f"""select sum(actual_qty) from tabBin
		where item_code=%s {condition}""",
		values,
	)[0][0]

	return actual_qty


def getProcessData(filters):

  # SQL query to calculate stock balances without warehouse breakdown
	return frappe.db.sql("""SELECT * FROM `tabItem` WHERE `disabled`=0""",as_dict=1)


def get_columns(filters):
	

	columns= []
	columns.append({'fieldname':'item_code','label':"Item Code",'fieldtype':'Link',"options":"Purchase Receipt",'align':'left','width':150})
	columns.append({'fieldname':'item_name','label':"Item Name",'fieldtype':'data','align':'left','width':200})
	columns.append({'fieldname':'safety_stock','label':"Safety Stock",'fieldtype':'data','align':'left','width':120})
	columns.append({'fieldname':'current_stock','label':"Current Stock",'fieldtype':'data','align':'left','width':120})
	columns.append({'fieldname':'below_safty','label':"Below Safety",'fieldtype':'data','align':'left','width':120})

	return columns