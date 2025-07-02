from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Consumed Item Code"), "fieldname": "consumed_item_code", "fieldtype": "Data", "width": 150},
        {"label": _("Consumed Item Name"), "fieldname": "consumed_item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Finished Product"), "fieldname": "finished_product", "fieldtype": "Data", "width": 150},
        {"label": _("Finished Product Name"), "fieldname": "finished_product_name", "fieldtype": "Data", "width": 200},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 100},
        {"label": _("BOM Name"), "fieldname": "bom_name", "fieldtype": "Data", "width": 150}
    ]

def get_data(filters):
    conditions = ""
    # If you want to add date filters or any other conditions, you can add them here
    # Example: conditions += "AND b.creation_date BETWEEN '{0}' AND '{1}'".format(filters.get("from_date"), filters.get("to_date"))

    data = frappe.db.sql("""
        SELECT 
            bi.item_code AS consumed_item_code, 
            bi.item_name AS consumed_item_name,
            b.item AS finished_product,
            b.item_name AS finished_product_name,
            bi.qty AS quantity,
            b.name AS bom_name
        FROM `tabBOM` AS b
        JOIN `tabBOM Item` AS bi ON bi.parent = b.name
    """, as_dict=True)

    return data
