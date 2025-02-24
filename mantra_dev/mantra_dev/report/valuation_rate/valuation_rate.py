# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from erpnext.stock.report.stock_balance.stock_balance import execute as stock_balance_execute


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 300},
		{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 300},
		{"label": "Valuation Rate", "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 200},
		{"label": "Balance Qty", "fieldname": "balance_qty", "fieldtype": "Float", "width": 200},
		{"label": "Balance Value", "fieldname": "balance_value", "fieldtype": "Currency", "width": 200},
	]


def get_data(filters):
	# This Report Function Give You Item Wise Current Stock Valutation Rate, Balance Qty, Balance Value from Stock Balance Report
	data = []
	item_wise_stock_balance = {}

	item_list_filters = {'disabled': 0}
	if filters.item_code:
		item_list_filters['name'] = ['in', filters.item_code]

	item_list = frappe.db.get_list("Item", item_list_filters, pluck="name")

	for item in item_list:
		stock_balance_filters = frappe._dict({
			'company': frappe.defaults.get_user_default("Company"),
			'from_date': frappe.utils.nowdate(),
			'to_date': frappe.utils.nowdate(),
			'item_code': item,
			'valuation_field_type': 'Currency'
		})
		# Generate Stock Balance report item-wise and calculate total balance, qty and valuation rate
		stock_balance_data = stock_balance_execute(filters=stock_balance_filters)
		if stock_balance_data:
			count = 0
			for stock in stock_balance_data[1]:
				# If warehouse filter is appiled then skip uneligible warehouse data
				if filters.warehouse and stock.warehouse not in filters.warehouse:
					continue
				else:
					count += 1

				if stock.item_code not in item_wise_stock_balance:
					item_wise_stock_balance[stock.item_code] = {
						'item_code': stock.item_code,
						'item_name': frappe.db.get_value("Item", stock.item_code, 'item_name'),
						'valuation_rate': 0,
						'balance_qty': 0,
						'balance_value': 0
					}
				
				item_wise_stock_balance[stock.item_code]['balance_qty'] += stock.bal_qty
				item_wise_stock_balance[stock.item_code]['balance_value'] += stock.bal_val

			if count > 0:
				item_wise_stock_balance[stock_balance_data[1][0].item_code]['valuation_rate'] = flt(item_wise_stock_balance[stock_balance_data[1][0].item_code]['balance_value']/item_wise_stock_balance[stock_balance_data[1][0].item_code]['balance_qty'])
				data.append(item_wise_stock_balance[stock_balance_data[1][0].item_code])

	return data






# def get_data(filters):
# 	# This Report Function Give You Item Wise Current Stock Valutation Rate, Balance Qty, Balance Value from Bin Doctype
# 	conditions = "b.actual_qty > 0"
# 	if filters.item_code:
# 		if len(filters.item_code) > 1:
# 			conditions += f" AND b.item_code IN {tuple(filters.item_code)}"
# 		else:
# 			conditions += f" AND b.item_code = '{filters.item_code[0]}'"
	
# 	if filters.warehouse:
# 		if len(filters.warehouse) > 1:
# 			conditions += f" AND b.warehouse IN {tuple(filters.warehouse)}"
# 		else:
# 			conditions += f" AND b.warehouse = '{filters.warehouse[0]}'"

# 	query = f"""
# 		SELECT
# 			b.item_code,
# 			it.item_name,
# 			AVG(b.valuation_rate) AS valuation_rate,
# 			SUM(b.actual_qty) AS balance_qty,
# 			SUM(b.stock_value) AS balance_value
# 		FROM
# 			`tabBin` AS b
# 		LEFT JOIN
# 			`tabItem` AS it ON it.name = b.item_code
# 		WHERE
# 			{conditions}
# 		GROUP BY
# 			b.item_code
# 	"""

# 	data = frappe.db.sql(query, as_dict=True)
# 	return data
