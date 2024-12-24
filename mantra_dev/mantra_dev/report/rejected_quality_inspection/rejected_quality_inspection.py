# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe import _




def execute(filters=None):
  columns, data = get_columns(), get_data(filters)
  return columns, data




def get_columns():
  return [
      {"label": _("Quality Inspection"), "fieldname": "VoucherNumber", "fieldtype": "Link", "options": "Quality Inspection", "width": 170},
      {"label": _("Status"), "fieldname": "Status", "fieldtype": "Data", "width": 70},
      {"label": _("Stock Entry"), "fieldname": "StockEntry", "fieldtype": "Link", "options": "Stock Entry", "width": 170},
      {"label": _("Date"), "fieldname": "Date", "fieldtype": "Date", "width": 100},
      {"label": _("Item Code"), "fieldname": "ItemCode", "fieldtype": "Link", "options": "Item", "width": 90},
      {"label": _("Item Name"), "fieldname": "ItemName", "fieldtype": "Data", "width": 100},
      {"label": _("QTY"), "fieldname": "Quantity", "fieldtype": "Float", "width": 80},
      {"label": _("Item Serial No"), "fieldname": "ItemSerialNo", "fieldtype": "Link", "options": "Serial No", "width": 100},
      {"label": _("Batch No"), "fieldname": "BatchNo", "fieldtype": "Link", "options": "Batch", "width": 100},
      {"label": _("Source Warehouse"), "fieldname": "SourceWarehouse", "fieldtype": "Link", "options": "Warehouse", "width": 120},
      {"label": _("Target Warehouse"), "fieldname": "TargetWarehouse", "fieldtype": "Link", "options": "Warehouse", "width": 120},
  ]




def get_data(filters):
  data = frappe.db.sql("""
       SELECT
           qi.name AS VoucherNumber,
           qi.status AS Status,
           qi.custom_rejected_stock_entry AS StockEntry,
           qi.item_serial_no AS ItemSerialNo,
           qi.batch_no AS BatchNo,
           se.posting_date AS Date,
           sed.item_code AS ItemCode,
           sed.item_name AS ItemName,
           sed.qty AS Quantity,
           sed.s_warehouse AS SourceWarehouse,
           sed.t_warehouse AS TargetWarehouse
        FROM
           `tabQuality Inspection` qi
        INNER JOIN
           `tabStock Entry` se ON se.name = qi.custom_rejected_stock_entry
        LEFT JOIN
           `tabStock Entry Detail` sed ON se.name = sed.parent
        WHERE
           qi.workflow_state = "Rejected"
        ORDER BY
           se.posting_date
     
  """, as_dict=True)
  return data

