# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt


import frappe
from frappe import _
import html


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": _("Stock Entry"), "fieldname": "stock_entry", "fieldtype": "Data", "width": 200},
        # "options": "Stock Entry",
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("Purchase Receipt"), "fieldname": "purchase_receipt", "fieldtype": "Data", "width": 150},
        # "options": "Purchase Receipt", 
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 150},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Data", "width": 200},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Data", "width": 100},
        {"label": _("Transfer Qty"), "fieldname": "transfer_qty", "fieldtype": "Float", "width": 100},
        {"label": _("QC Done Qty"), "fieldname": "qc_done_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Batch No"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 150},
        {"label": _("Create QC"), "fieldname": "CreateQC", "fieldtype": "Button", "width": 110},
    ]

def get_data(filters):
    
    # Fetch QC warehouses from `tabSingles` table
    qc_warehouse = frappe.db.sql("""
        SELECT value 
        FROM `tabSingles` 
        WHERE doctype = 'QC Settings' 
        AND field = 'default_qc_processing_warehouse'
    """, as_dict=True)

    if not qc_warehouse or not qc_warehouse[0].get("value"):
        frappe.throw(_("No QC Processing Warehouse found. Please configure it in QC Settings."))

    default_qc_processing_warehouse = qc_warehouse[0]["value"]

    # Fetch stock entry details for QC-related warehouses
    stock_data = frappe.db.sql("""
        SELECT 
            se.name AS stock_entry, 
            se.posting_date, 
            sed.reference_purchase_receipt AS purchase_receipt,
            sed.item_code, 
            sed.item_name, 
            sed.item_group, 
            sed.t_warehouse AS warehouse, 
            COALESCE(sed.stock_uom, sed.uom) AS stock_uom,
            sed.transfer_qty,
            sed.custom_qc_done_qty AS qc_done_qty,
            sed.batch_no,
            (sed.transfer_qty - IFNULL(sed.custom_qc_done_qty, 0)) AS actual_qty            
        FROM `tabStock Entry` se
        JOIN `tabStock Entry Detail` sed ON se.name = sed.parent
        JOIN `tabItem` item ON sed.item_code = item.item_code
        WHERE se.docstatus = 1
        AND sed.t_warehouse = %s
        AND sed.custom_qc_done_qty < sed.transfer_qty
        ORDER BY se.posting_date, sed.item_code
    """, (default_qc_processing_warehouse), as_dict=True)


    # Add button dynamically
    for row in stock_data:

        row["CreateQC"] = f"""
                <button class="btn btn-primary pt-0 pb-0 create_qc" 
                    data-item_code="{html.escape(row["item_code"] or "")}" 
                    data-batch_no="{html.escape(row["batch_no"] or "")}" 
                    data-stock_entry="{html.escape(row["stock_entry"] or "")}" 
                    data-transfer_qty="{row["transfer_qty"] if row["transfer_qty"] is not None else "0"}"
                    data-actual_qty="{row.get('actual_qty', '0')}"
                    style="background-color: grey">
                    Create QC
                </button>
            """

    return stock_data

