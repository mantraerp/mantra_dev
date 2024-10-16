from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Shipment"), "fieldname": "shipment", "fieldtype": "Data"},	
        {"label": _("Delivery Note No"), "fieldname": "delivery_note_no", "fieldtype": "Link", "options": "Delivery Note", "width": 200},
        {"label": _("Custom Sales Invoice No"), "fieldname": "custom_sales_invoice_no", "fieldtype": "Data", "width": 200},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("Document Status"), "fieldname": "docstatus", "fieldtype": "Int", "width": 100},
        {"label": _("Shipping Address Name"), "fieldname": "shipping_address_name", "fieldtype": "Data", "width": 200},
        {"label": _("Shipping Address"), "fieldname": "shipping_address", "fieldtype": "Data", "width": 300},
        {"label": _("Dispatch Address Name"), "fieldname": "dispatch_address_name", "fieldtype": "Data", "width": 200},
        {"label": _("Dispatch Address"), "fieldname": "dispatch_address", "fieldtype": "Data", "width": 300},
        
    ]

def get_data(filters):
    conditions = ""
    if filters.get("customer"):
        conditions += " AND customer_name = %(customer)s"
    if filters.get("custom_sales_invoice_no"):
        conditions += " AND custom_sales_invoice_no = %(custom_sales_invoice_no)s"

    data = frappe.db.sql("""
        SELECT
            name AS delivery_note_no,
            custom_sales_invoice_no AS custom_sales_invoice_no,
            customer_name AS customer_name,
            posting_date AS posting_date,
            docstatus AS docstatus,
            shipping_address_name AS shipping_address_name,
            shipping_address AS shipping_address,
            dispatch_address_name AS dispatch_address_name,
            dispatch_address AS dispatch_address
        FROM
            `tabDelivery Note`
        WHERE
            docstatus = 1 and custom_shipment_createed=0
            {conditions}
        ORDER BY
            posting_date DESC
    """.format(conditions=conditions), filters, as_dict=True)
    
    for row in data:
        row["shipment"] = '<button class="btn btn-primary pt-0 pb-0 create-shipment" data-id="{}">Shipment</button>'.format(row["delivery_note_no"])
    
    return data
@frappe.whitelist()
def create_shipment(delivery_note_no):
    dc_id=frappe.get_doc("Delivery Note",delivery_note_no)
    dc_id
    frappe.msgprint("function called")
    return "Done"