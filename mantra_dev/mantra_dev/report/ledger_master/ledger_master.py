from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data()
    return columns, data

def get_columns():
    return [
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Group Name"), "fieldname": "group_name", "fieldtype": "Data", "width": 150},
        {"label": _("Contact No"), "fieldname": "contact_no", "fieldtype": "Data", "width": 150},
        {"label": _("Email Id"), "fieldname": "email_id", "fieldtype": "Data", "width": 200},
        {"label": _("State"), "fieldname": "state", "fieldtype": "Data", "width": 100},
        {"label": _("Country"), "fieldname": "country", "fieldtype": "Data", "width": 100},
        {"label": _("PIN"), "fieldname": "pin", "fieldtype": "Data", "width": 100},
        {"label": _("Address Line 1"), "fieldname": "address_line1", "fieldtype": "Data", "width": 200},
        {"label": _("Address Line 2"), "fieldname": "address_line2", "fieldtype": "Data", "width": 200},
        {"label": _("Address Line 3"), "fieldname": "address_line3", "fieldtype": "Data", "width": 200},
        {"label": _("Alias"), "fieldname": "alias", "fieldtype": "Data", "width": 150},
        {"label": _("PAN"), "fieldname": "pan", "fieldtype": "Data", "width": 150},
        {"label": _("GST No"), "fieldname": "gst_no", "fieldtype": "Data", "width": 150}
    ]

def get_data():
    data = frappe.db.sql("""
        SELECT 
            c.customer_name AS customer_name,
            cpa.account AS group_name,
            c.mobile_no AS contact_no,
            c.email_id AS email_id,
            a.state AS state,
            a.country AS country,
            a.pincode AS pin,
            a.address_line1 AS address_line1,
            a.address_line2 AS address_line2,
            a.city AS address_line3,
            c.name AS alias,
            c.pan AS pan,
            c.gstin AS gst_no
        FROM `tabCustomer` AS c
        JOIN `tabDynamic Link` AS dl ON dl.link_name = c.name
        JOIN `tabAddress` AS a ON a.name = dl.parent
        JOIN `tabParty Account` AS cpa ON c.name = cpa.parent
    """, as_dict=True)

    return data
