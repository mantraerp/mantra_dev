from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 150},
        {"label": _("Voucher Number"), "fieldname": "voucher_number", "fieldtype": "Data", "width": 150},
        {"label": _("Reference"), "fieldname": "reference", "fieldtype": "Data", "width": 150},
        {"label": _("Bill Date"), "fieldname": "bill_date", "fieldtype": "Date", "width": 100},
        {"label": _("Reference Type"), "fieldname": "reference_type", "fieldtype": "Data", "width": 150},
        {"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Data", "width": 150},
        {"label": _("Account"), "fieldname": "account", "fieldtype": "Data", "width": 150},
        {"label": _("Ledger Amount"), "fieldname": "ledger_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Amt Type"), "fieldname": "amt_type", "fieldtype": "Data", "width": 100},
        {"label": _("Final Narration"), "fieldname": "final_narration", "fieldtype": "Data", "width": 150}
    ]

def get_data(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += "jv.posting_date BETWEEN '{0}' AND '{1}'".format(filters.get("from_date"), filters.get("to_date"))
    
    data = frappe.db.sql("""
        SELECT
            jv.posting_date AS posting_date,
            jv.voucher_type AS voucher_type,
            jv.name AS voucher_number,
            jea.reference_name AS reference,
            jv.bill_date AS bill_date,
            jea.reference_type AS reference_type,
            jea.cost_center AS cost_center,
            jea.account AS account,
            jv.total_amount AS ledger_amount,
            jv.total_amount_currency AS amt_type,
            jea.user_remark AS final_narration
        FROM
            `tabJournal Entry` AS jv
        JOIN
            `tabJournal Entry Account` AS jea ON jv.name = jea.parent
        WHERE
            jv.docstatus = 1 AND {conditions}
    """.format(conditions=conditions), as_dict=True)

    return data
