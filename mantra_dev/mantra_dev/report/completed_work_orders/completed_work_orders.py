# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

# import frappe


from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data()
    return columns, data

def get_columns():
    return [
        {"label": _("Work Order"), "fieldname": "work_order", "fieldtype": "Link", "options": "Work Order", "width": 200},
        {"label": _("Date"), "fieldname": "creation", "fieldtype": "Date", "width": 120},
        {"label": _("Item"), "fieldname": "production_item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("To Produce"), "fieldname": "to_produce", "fieldtype": "Int", "width": 100},
        {"label": _("Produced"), "fieldname": "produced", "fieldtype": "Int", "width": 100},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
    ]

def get_data():
    return frappe.db.sql("""
        SELECT
            `tabWork Order`.name AS work_order,
            `tabWork Order`.creation AS creation,
            `tabWork Order`.production_item AS production_item,
            `tabWork Order`.qty AS to_produce,
            `tabWork Order`.produced_qty AS produced,
            `tabWork Order`.company AS company
        FROM
            `tabWork Order`
        WHERE
            `tabWork Order`.docstatus = 1
            AND IFNULL(`tabWork Order`.produced_qty, 0) >= `tabWork Order`.qty
    """, as_dict=True)
