from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("VoucherType"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 150},
        {"label": _("VoucherNumber"), "fieldname": "voucher_number", "fieldtype": "Link", "options": "Purchase Invoice", "width": 150},
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Supplier Inv No"), "fieldname": "supplier_inv_no", "fieldtype": "Data", "width": 150},
        {"label": _("Sup. Date"), "fieldname": "sup_date", "fieldtype": "Date", "width": 100},
        {"label": _("PartyName"), "fieldname": "party_name", "fieldtype": "Data", "width": 200},
        {"label": _("Approval Status"), "fieldname": "approval_status", "fieldtype": "Data", "width": 150},
        {"label": _("TaxName"), "fieldname": "tax_name", "fieldtype": "Data", "width": 150},
        {"label": _("Add or Deduct"), "fieldname": "add_deduct_tax", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate"), "fieldname": "tax_rate", "fieldtype": "Float", "width": 100},
        {"label": _("TaxAmount"), "fieldname": "tax_amount", "fieldtype": "Float", "width": 100},
        {"label": _("Department/Class"), "fieldname": "department_class", "fieldtype": "Link", "options": "Cost Center", "width": 150}
    ]

def get_data(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions = "pi.posting_date BETWEEN '{0}' AND '{1}'".format(filters.get("from_date"), filters.get("to_date"))
    
    data = frappe.db.sql("""
        SELECT
            pi.custom_invoice_type AS voucher_type,
            pi.name AS voucher_number,
            pi.posting_date AS date,
            pi.bill_no AS supplier_inv_no,
            pi.bill_date AS sup_date,
            pi.supplier_name AS party_name,
            pi.workflow_state AS approval_status,
            pt.account_head AS tax_name,
            pt.add_deduct_tax AS add_deduct_tax,
            pt.rate AS tax_rate,
            pt.tax_amount AS tax_amount,
            pi.cost_center AS department_class
        FROM
            `tabPurchase Invoice` AS pi
        JOIN
            `tabPurchase Invoice Item` AS pii ON pii.parent = pi.name
        LEFT JOIN
            `tabPurchase Taxes and Charges` AS pt ON pt.parent = pi.name
        WHERE
            pi.docstatus = 1
            AND {conditions}
        ORDER BY
            pii.parent
    """.format(conditions=conditions), as_dict=True)

    return data
