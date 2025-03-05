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
      {"label": _("Accepted QTY"), "fieldname": "AcceptedQTY", "fieldtype": "Int", "width": 70},
      {"label": _("Warehouse"), "fieldname": "Warehouse", "fieldtype": "Data", "width": 150},
      {"label": _("Inspection Required"), "fieldname": "InspectionRequired", "fieldtype": "Check", "width": 70},
      {"label": _("Stock Entry"), "fieldname": "StockEntry", "fieldtype": "Link", "options": "Stock Entry", "width": 170},
      {"label": _("Approve"), "fieldname": "Approve", "fieldtype": "Button", "width": 90},
  
  ]

def get_data(filters):

    # Fetch the default inward warehouse from QC Settings
    inward_warehouse = frappe.db.get_value("QC Settings", "QC Settings", "default_inward_warehouse")

    if not inward_warehouse:
        frappe.throw(_("Default Inward Warehouse is not set in QC Settings."))

    data = frappe.db.sql("""
                       
    SELECT
        se.name AS StockEntry,
        sed.item_code AS ItemCode,
        sed.item_name AS ItemName,
        sed.qty AS AcceptedQTY,
        sed.t_warehouse AS Warehouse,
        pr.name AS VoucherNumber,
        pr.posting_date AS Date,
        sed.custom_inspection_required_before_transfer_warehouse AS InspectionRequired,
        CONCAT(
           '<button class="btn btn-primary pt-0 pb-0 approvestockentry" style="background-color: grey" ',
           'data-stock_entry="', se.name, '" ',
           'data-item_code="', sed.item_code, '" ',
           'data-qty="', sed.qty, '" ',
           'data-purchase_receipt="', pr.name, '" ',
           '>Approve</button>'
       ) AS Approve
    FROM
        `tabStock Entry` se
    JOIN
        `tabStock Entry Detail` sed ON sed.parent = se.name
    INNER JOIN
        `tabPurchase Receipt` pr ON pr.name = sed.reference_purchase_receipt
    WHERE
        se.docstatus = 0 
        AND
        sed.s_warehouse = %s
    ORDER BY
        pr.posting_date;
    
    
    """, (inward_warehouse,), as_dict=True)
    return data

