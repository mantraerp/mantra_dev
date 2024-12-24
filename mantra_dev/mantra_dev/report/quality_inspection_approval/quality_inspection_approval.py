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
      {"label": _("Date"), "fieldname": "Date", "fieldtype": "Date", "width": 100},
      {"label": _("Status"), "fieldname": "Status", "fieldtype": "Data", "width": 80},
      {"label": _("Item Code"), "fieldname": "ItemCode", "fieldtype": "Link", "options": "Item", "width": 90},
      {"label": _("Item Name"), "fieldname": "ItemName", "fieldtype": "Data", "width": 150},
      {"label": _("Item Serial No"), "fieldname": "ItemSerialNo", "fieldtype": "Link", "options": "Serial No", "width": 100},
      {"label": _("Batch No"), "fieldname": "BatchNo", "fieldtype": "Link", "options": "Batch", "width": 100},
      {"label": _("Sample Size"), "fieldname": "SampleSize", "fieldtype": "Float", "width": 90},
      {"label": _("Quality Inspection Template"), "fieldname": "QualityInspectionTemplate", "fieldtype": "Link", "options": "Quality Inspection Template", "width": 120},
      {"label": _("Approve"), "fieldname": "Approve", "fieldtype": "Button", "width": 90},
  ]




def get_data(filters):
  data = frappe.db.sql("""
      SELECT
          qi.name AS VoucherNumber,
          qi.report_date AS Date,
          qi.status AS Status,
          qi.item_code AS ItemCode,
          qi.item_name AS ItemName,
          qi.item_serial_no AS ItemSerialNo,
          qi.batch_no AS BatchNo,
          qi.sample_size AS SampleSize,
          qi.quality_inspection_template AS QualityInspectionTemplate,
       CONCAT(
           '<button class="btn btn-primary pt-0 pb-0 approve" style="background-color: white" ',
           'data-quality_inspection="', qi.name, '" ',
           'data-status="', qi.status, '" ',
           '>Approve</button>'
       ) AS Approve




      FROM
          `tabQuality Inspection` qi
      WHERE
          qi.workflow_state = "Approval Requested"
      ORDER BY
          qi.report_date
  """, as_dict=True)
  return data

