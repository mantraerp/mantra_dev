# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

# import frappe


import frappe
import traceback
from frappe.utils import cstr, flt
def execute(filters=None):
	columns, data = [], []


	try:
		columns = get_columns(filters)
		data_raw = getProcessData(filters)
		item_code_stock = {} 
		current_stock_data = get_latest_stock_qty()  
		for warehouse, items in current_stock_data.items():
			warehouse_doc = frappe.get_doc("Warehouse", warehouse)
			if warehouse_doc.custom_is_not_countable == 0:
				for item_code, qty in items.items():
					if item_code in item_code_stock:
						item_code_stock[item_code] += qty  
					else:
						item_code_stock[item_code] = qty
		
		for index, row in enumerate(data_raw):

			safty_stock = row['safety_stock']
			if safty_stock in [None, ""]:
				safty_stock = 0

			item_code = row['item_code']
			current_stock = item_code_stock.get(item_code, 0) 
			# current_stock=get_latest_stock_qty2(row['item_code']) 
			if safty_stock > current_stock:
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


def get_latest_stock_qty2(item_code):
	values, condition = [item_code], ""
	actual_qty = frappe.db.sql(
		f"""select sum(actual_qty) from tabBin
		where item_code=%s {condition}""",
		values,
	)[0][0]

	return actual_qty


def get_latest_stock_qty():
	bin_map = {}
	for d in frappe.db.sql(
		"""SELECT item_code, warehouse, actual_qty as qty
		FROM tabBin""",
		as_dict=1,
	):
		bin_map.setdefault(d.warehouse, {}).setdefault(d.item_code, flt(d.qty))
   
	return bin_map	




def getProcessData(filters):

  # SQL query to calculate stock balances without warehouse breakdown
	return frappe.db.sql("""SELECT * FROM `tabItem` WHERE `disabled`=0""",as_dict=1)


def get_columns(filters):
	

	columns= []
	columns.append({'fieldname':'item_code','label':"Item Code",'fieldtype':'Link',"options":"Item",'align':'left','width':150})
	columns.append({'fieldname':'item_name','label':"Item Name",'fieldtype':'data','align':'left','width':200})
	columns.append({'fieldname':'safety_stock','label':"Safety Stock",'fieldtype':'data','align':'left','width':120})
	columns.append({'fieldname':'current_stock','label':"Current Stock",'fieldtype':'data','align':'left','width':120})
	columns.append({'fieldname':'below_safty','label':"Below Safety",'fieldtype':'data','align':'left','width':120})

	return columns