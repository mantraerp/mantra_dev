# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe import _




def execute(filters=None):
  columns, data = get_columns(), get_data(filters)
  return columns, data




def get_columns():
  return [
      {"label": _("Purchase Receipt"), "fieldname": "VoucherNumber", "fieldtype": "Data", "width": 200},
      {"label": _("Date"), "fieldname": "Date", "fieldtype": "Date", "width": 100},
      {"label": _("Item Code"), "fieldname": "ItemCode", "fieldtype": "Link", "options": "Item", "width": 100},
      {"label": _("Item Name"), "fieldname": "ItemName", "fieldtype": "Data", "width": 150},
      {"label": _("Received QTY"), "fieldname": "ReceivedQTY", "fieldtype": "Float", "width": 100},
      {"label": _("Accepted QTY"), "fieldname": "AcceptedQTY", "fieldtype": "Float", "width": 100},
      {"label": _("QC Processing QTY"), "fieldname": "QCProcessingQTY", "fieldtype": "Float", "width": 100},
      {"label": _("QC Remaining QTY"), "fieldname": "QCRemainingQTY", "fieldtype": "Float", "width": 100},
      {"label": _("Warehouse"), "fieldname": "Warehouse", "fieldtype": "Data", "width": 150},
      {"label": _("Inspection Required"), "fieldname": "InspectionRequired", "fieldtype": "Check", "width": 70},
      {"label": _("QC Request"), "fieldname": "QCRequest", "fieldtype": "Button", "width": 115},
      {"label": _("Stock Transfer"), "fieldname": "StockTransfer", "fieldtype": "Button", "width": 135},
  ]




def get_data(filters):

  # Fetch the default inward warehouse from QC Settings
  inward_warehouse = frappe.db.get_value("QC Settings", "QC Settings", "default_inward_warehouse")

  if not inward_warehouse:
        frappe.throw(_("Default Inward Warehouse is not set in QC Settings."))

  data = frappe.db.sql("""
      SELECT
          pr.name AS VoucherNumber,
          pr.posting_date AS Date,
          pri.item_code AS ItemCode,
          pri.item_name AS ItemName,
          pri.received_qty AS ReceivedQTY,
          pri.qty AS AcceptedQTY,
          pri.custom_qc_processing_quantity AS QCProcessingQTY,
          pri.custom_qc_remaining_quantity AS QCRemainingQTY,
          pri.warehouse AS Warehouse,
          pri.custom_inspection_required_before_transfer_warehouse AS InspectionRequired,
       CASE
           WHEN pri.custom_inspection_required_before_transfer_warehouse = 1 THEN
               CONCAT(
                   '<button class="btn btn-primary pt-0 pb-0 qcrequest" style="background-color: grey" ',
                   'data-id="', pr.name, '" ',
                   'data-purchase-receipt-item-id="', pri.name, '" ',
                   'data-item_code="', pri.item_code, '" ',
                   'data-accepted_quantity="', pri.qty, '" ',
                   'data-qc_processing_quantity="', pri.custom_qc_processing_quantity, '" ',
                   'data-qc_remaining_quantity="', pri.custom_qc_remaining_quantity, '" ',
                   'data-warehouse="', pri.warehouse, '" ',
                   '>QC Request</button>'
               )
           ELSE
               ''
       END AS QCRequest,
       CASE
           WHEN pri.custom_inspection_required_before_transfer_warehouse = 0 THEN
               CONCAT(
                   '<button class="btn btn-primary pt-0 pb-0 stocktransfer" style="background-color: grey" ',
                   'data-id="', pr.name, '" ',
                   'data-purchase-receipt-item-id="', pri.name, '" ',
                   'data-item_code="', pri.item_code, '" ',
                   'data-accepted_quantity="', pri.qty, '" ',
                   'data-qc_processing_quantity="', pri.custom_qc_processing_quantity, '" ',
                   'data-qc_remaining_quantity="', pri.custom_qc_remaining_quantity, '" ',
                   'data-warehouse="', pri.warehouse, '" ',
                   '>Stock Transfer</button>'
               )
           ELSE
               ''
       END AS StockTransfer

      FROM
          `tabPurchase Receipt` pr
      JOIN
          `tabPurchase Receipt Item` AS pri ON pri.parent = pr.name
      WHERE
          pr.docstatus = 1 AND
          pr.is_return = 0 AND
          pr.is_subcontracted = 0 AND
          pri.warehouse = %s AND
          (pri.custom_qc_remaining_quantity != 0)
      ORDER BY
          pr.posting_date, pr.name
  """,(inward_warehouse,), as_dict=True)
  return data
