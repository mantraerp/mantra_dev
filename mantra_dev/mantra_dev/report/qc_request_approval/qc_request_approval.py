# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe import _




def execute(filters=None):
  columns, data = get_columns(), get_data(filters)
  return columns, data




def get_columns():
  return [
      {"label": _("Purchase Receipt"), "fieldname": "VoucherNumber", "fieldtype": "Link", "options": "Purchase Receipt", "width": 200},
      {"label": _("Date"), "fieldname": "Date", "fieldtype": "Date", "width": 100},
      {"label": _("Item Code"), "fieldname": "ItemCode", "fieldtype": "Link", "options": "Item", "width": 100},
      {"label": _("Item Name"), "fieldname": "ItemName", "fieldtype": "Data", "width": 150},
      {"label": _("Received QTY"), "fieldname": "ReceivedQTY", "fieldtype": "Int", "width": 70},
      {"label": _("Accepted QTY"), "fieldname": "AcceptedQTY", "fieldtype": "Int", "width": 70},
      {"label": _("Warehouse"), "fieldname": "Warehouse", "fieldtype": "Data", "width": 150},
      {"label": _("Inspection Required"), "fieldname": "InspectionRequired", "fieldtype": "Check", "width": 70},
      {"label": _("Stock Entry"), "fieldname": "StockEntry", "fieldtype": "Link", "options": "Stock Entry", "width": 170},
      {"label": _("Approve"), "fieldname": "Approve", "fieldtype": "Button", "width": 90},
  
  ]




def get_data(filters):
  data = frappe.db.sql("""
      SELECT
          pr.name AS VoucherNumber,
          pr.posting_date AS Date,
          pri.item_code AS ItemCode,
          pri.item_name AS ItemName,
          pri.received_qty AS ReceivedQTY,
          pri.qty AS AcceptedQTY,
          pri.warehouse AS Warehouse,
          i.custom_inspection_required_before_transfer_warehouse AS InspectionRequired,
          pri.custom_stock_entry AS StockEntry,
       CONCAT(
           '<button class="btn btn-primary pt-0 pb-0 approvestockentry" style="background-color: grey" ',
           'data-stock_entry="', pri.custom_stock_entry, '" ',
           '>Approve</button>'
       ) AS Approve




      FROM
          `tabPurchase Receipt` pr
      JOIN
          `tabPurchase Receipt Item` pri ON pri.parent = pr.name
      JOIN
          `tabItem` i ON i.name = pri.item_code
      LEFT JOIN
           `tabStock Entry` se ON se.name = pri.custom_stock_entry
      WHERE
          pr.docstatus = 1 AND
          pr.is_return = 0 AND
          pri.custom_stock_entry IS NOT NULL AND
          se.docstatus = 0
      ORDER BY
          pr.posting_date
  """, as_dict=True)
  return data
