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
      {"label": _("Received QTY"), "fieldname": "ReceivedQTY", "fieldtype": "Int", "width": 100},
      {"label": _("Accepted QTY"), "fieldname": "AcceptedQTY", "fieldtype": "Int", "width": 100},
      {"label": _("Warehouse"), "fieldname": "Warehouse", "fieldtype": "Data", "width": 150},
      {"label": _("Inspection Required"), "fieldname": "InspectionRequired", "fieldtype": "Check", "width": 70},
      {"label": _("QC Request"), "fieldname": "QCRequest", "fieldtype": "Button", "width": 115},
      {"label": _("Stock Transfer"), "fieldname": "StockTransfer", "fieldtype": "Button", "width": 135},
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
       CASE
           WHEN i.custom_inspection_required_before_transfer_warehouse = 1 THEN
               CONCAT(
                   '<button class="btn btn-primary pt-0 pb-0 qcrequest" style="background-color: white" ',
                   'data-id="', pr.name, '" ',
                   'data-pr-date="', pr.posting_date, '" ',
                   'data-item_code="', pri.item_code, '" ',
                   'data-item_name="', pri.item_name, '" ',
                   'data-item-code="', pri.item_code, '" ',
                   'data-received_qty="', pri.received_qty, '" ',
                   'data-qty="', pri.qty, '" ',
                   'data-warehouse="', pri.warehouse, '" ',
                   'data-custom_inspection_required_before_transfer_warehouse="', i.custom_inspection_required_before_transfer_warehouse, '" ',
                   '>QC Request</button>'
               )
           ELSE
               ''
       END AS QCRequest,
       CASE
           WHEN i.custom_inspection_required_before_transfer_warehouse = 0 THEN
               CONCAT(
                   '<button class="btn btn-primary pt-0 pb-0 stocktransfer" style="background-color: white" ',
                   'data-id="', pr.name, '" ',
                   'data-pr-date="', pr.posting_date, '" ',
                   'data-item_code="', pri.item_code, '" ',
                   'data-item_name="', pri.item_name, '" ',
                   'data-item-code="', pri.item_code, '" ',
                   'data-received_qty="', pri.received_qty, '" ',
                   'data-qty="', pri.qty, '" ',
                   'data-warehouse="', pri.warehouse, '" ',
                   'data-custom_inspection_required_before_transfer_warehouse="', i.custom_inspection_required_before_transfer_warehouse, '" ',
                   '>Stock Transfer</button>'
               )
           ELSE
               ''
       END AS StockTransfer




      FROM
          `tabPurchase Receipt` pr
      JOIN
          `tabPurchase Receipt Item` AS pri ON pri.parent = pr.name
      JOIN
          `tabItem` AS i ON i.name = pri.item_code
      WHERE
          pr.docstatus = 1 AND
          pr.is_return = 0 AND
          (pri.custom_stock_entry IS NULL OR pri.custom_stock_entry = '')
      ORDER BY
          pr.posting_date
  """, as_dict=True)
  return data
