# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt



import frappe
from frappe.utils import flt


def execute(filters=None):
	columns, data = [], []
  
	if filters.get('from_date') is not None:
		data_raw = getProcessData(filters.get('from_date'))
	else:
		data_raw = getProcessData()
	
	if len(data_raw) > 0:
		columns = get_columns(filters)
		for index,row in enumerate(data_raw):
			current_stock = get_latest_stock_qty(row['item_code'])
			total_quantity = (flt(current_stock) if current_stock not in [None, 'null'] else 0) + flt(row['total_qty'])
			data.append([
				row['item_code'],
				row['item_name'],
				current_stock if current_stock not in [None,'null'] else 0,
				row['total_qty'],
				total_quantity
			])
		return columns,data
 
def get_latest_stock_qty(item_code):
	values, condition = [item_code], ""
	actual_qty = frappe.db.sql(
		f"""select sum(actual_qty) from tabBin
		where item_code=%s {condition}""",
		values,
	)[0][0]

	return actual_qty

def getProcessData(date_filter=None):
	query = """
		SELECT
			po.item_code,
			po.item_name,
			SUM(po.expected_qty) AS total_qty
		FROM
			`tabPurchase Order Expected Date` po
		WHERE
			po.status = 'Approved'
	"""
	
	if date_filter:
		query += " AND po.final_expected_receive_date < %s"
	query += " GROUP BY po.item_code, po.item_name HAVING total_qty IS NOT NULL"

	return frappe.db.sql(query, (date_filter,) if date_filter else (), as_dict=True)


def get_columns(filters):
	

	columns= []
	columns.append({'fieldname':'item_code','label':"Item Code",'fieldtype':'Link',"options":"Item",'align':'left','width':150})
	columns.append({'fieldname':'item_name','label':"Item Name",'fieldtype':'data','align':'left','width':200})
	columns.append({'fieldname':'actual_stock','label':"Actual Qty",'fieldtype':'float','align':'left','width':120})
	columns.append({'fieldname':'in_transit','label':"In Transit Qty",'fieldtype':'float','align':'left','width':120})
	columns.append({'fieldname':'total_quantity','label':"Total Projected Qty",'fieldtype':'float','align':'left','width':150})

	return columns