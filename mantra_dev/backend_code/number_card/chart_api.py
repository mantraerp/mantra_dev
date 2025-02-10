import frappe
from frappe import _


@frappe.whitelist()
def get_top_items_by_value(from_date,to_date,limit=10):
    # Getting Top Items Of Out Qty Of Stock Ledger By Value With Limited Records
    if not from_date or not to_date:
        frappe.throw(_("Please Enter From Date Or To Date"))
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    items = """
        SELECT
           sle.item_code,
           SUM(sle.actual_qty * -1 * sle.valuation_rate) AS total_value
        FROM
            `tabStock Ledger Entry` AS sle
        WHERE
            sle.posting_date BETWEEN %s AND %s
            AND sle.actual_qty < 0
            AND sle.is_cancelled = 0
        GROUP BY
            sle.item_code
        HAVING
            total_value > 0
        ORDER BY
            total_value DESC
        LIMIT %s
    """

    data = frappe.db.sql(items,(from_date, to_date,limit),as_dict=True)
    return data


@frappe.whitelist()
def get_top_items_by_qty(from_date=None,to_date=None,limit=10):
    # Getting Top Items Of Out Qty Of Stock Ledger By Qty With Limited Records
    if not from_date or not to_date:
        frappe.throw(_("Please Enter From Date Or To Date"))
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    items = """
        SELECT
            sle.item_code,
            SUM(sle.actual_qty * -1) AS total_qty
        FROM
            `tabStock Ledger Entry` AS sle
        WHERE
            sle.posting_date BETWEEN %s AND %s
            AND sle.actual_qty < 0
            AND sle.is_cancelled = 0
        GROUP BY
            sle.item_code
        HAVING
            total_qty > 0
        ORDER BY
            total_qty DESC
        LIMIT %s
    """

    data = frappe.db.sql(items,(from_date, to_date,limit),as_dict=True)
    return data