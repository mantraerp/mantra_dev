from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("PO No"), "fieldname": "po_no", "fieldtype": "Link", "options": "Purchase Order", "width": 150},
        {"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 200},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 150},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": _("Received Qty"), "fieldname": "received_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Pending Qty"), "fieldname": "pending_qty", "fieldtype": "Float", "width": 100}
    ]

def get_data(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions = "po.transaction_date BETWEEN '{0}' AND '{1}'".format(filters.get("from_date"), filters.get("to_date"))
    
    data = frappe.db.sql("""
        SELECT
            po.name AS po_no,
            po.supplier_name AS supplier_name,
            poi.item_code AS item_code,
            poi.item_name AS item_name,
            po.status AS status,
            poi.qty AS qty,
            poi.received_qty AS received_qty,
            poi.qty - poi.received_qty AS pending_qty
        FROM
            `tabPurchase Order` AS po
        JOIN
            `tabPurchase Order Item` AS poi ON poi.parent = po.name
        WHERE
            (po.status = 'To Receive' OR po.status = 'To Receive and Bill')
            AND {conditions}
        ORDER BY
            po.transaction_date DESC
    """.format(conditions=conditions), as_dict=True)

    return data
