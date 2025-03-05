# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import html


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 150},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Data", "width": 200},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Data", "width": 100},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 120},
    ]

def get_data(filters):
    # Fetch QC warehouses from `tabSingles` table
    qc_warehouses = frappe.db.sql("""
        SELECT field, value 
        FROM `tabSingles` 
        WHERE doctype = 'QC Settings' 
        AND field IN ('default_qc_processing_warehouse', 'default_qc_rejected_warehouse', 'default_rework_warehouse', 'default_return_warehouse')
    """, as_dict=True)

    # Extract warehouse values and filter out None values
    qc_warehouses_list = [row["value"] for row in qc_warehouses if row["value"]]

    # Ensure at least one warehouse is found
    if not qc_warehouses_list:
        frappe.throw(_("No QC warehouses found. Please configure QC warehouses in QC Settings."))

    # If user selects warehouses in filter, override default QC warehouses
    if filters and filters.get("warehouse"):
        selected_warehouses = filters.get("warehouse")
    else:
        selected_warehouses = qc_warehouses_list

     # Ensure at least one warehouse is found
    if not selected_warehouses:
        frappe.throw(_("No QC warehouses found. Please configure QC warehouses in QC Settings."))

    # Convert list to tuple for SQL query
    qc_warehouses_tuple = tuple(selected_warehouses)

    # Fetch stock balances only for QC-related warehouses
    stock_data = frappe.db.sql("""
        SELECT 
            bin.item_code, item.item_name, item.item_group, 
            bin.warehouse, item.stock_uom, bin.actual_qty AS balance_qty
        FROM `tabBin` bin
        JOIN `tabItem` item ON bin.item_code = item.item_code
        WHERE bin.warehouse IN %(qc_warehouses)s
        ORDER BY bin.item_code, bin.warehouse
    """, {"qc_warehouses": qc_warehouses_tuple}, as_dict=True)

    return stock_data

@frappe.whitelist()
def get_qc_warehouses():
    """Fetch QC warehouses from QC Settings and return properly formatted data."""
    qc_warehouses = frappe.db.sql("""
        SELECT value, '' as description
        FROM `tabSingles` 
        WHERE doctype = 'QC Settings' 
        AND field IN ('default_qc_processing_warehouse', 'default_qc_rejected_warehouse', 'default_rework_warehouse', 'default_return_warehouse')
    """, as_dict=True)

    # Return a structured list of dictionaries for MultiSelectList
    return qc_warehouses
