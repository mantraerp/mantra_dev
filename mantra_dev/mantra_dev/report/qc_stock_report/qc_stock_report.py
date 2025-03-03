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
    qc_warehouses = frappe.db.sql("""
        SELECT field, value 
        FROM `tabSingles` 
        WHERE doctype = 'QC Settings' 
        AND field IN ('default_qc_processing_warehouse')
    """, as_dict=True)

    # AND field IN ('default_qc_processing_warehouse', 'default_qc_rejected_warehouse', 'default_rework_warehouse', 'default_return_warehouse')

    # Extract warehouse values and filter out None values
    qc_warehouses_list = [row["value"] for row in qc_warehouses if row["value"]]
    default_qc_processing_warehouse = next(
        (row["value"] for row in qc_warehouses if row["field"] == "default_qc_processing_warehouse" and row["value"]),
        None
    )

    # Ensure at least one warehouse is found
    if not qc_warehouses_list:
        frappe.throw(_("No QC warehouses found. Please configure QC warehouses in QC Settings."))

    # If user selects warehouses in filter, override default QC warehouses
    if filters and filters.get("warehouse"):
        selected_warehouses = filters.get("warehouse")
    else:
        selected_warehouses = qc_warehouses_list

    # Ensure at least one warehouse is found
    if not selected_warehouses:
        frappe.throw(_("No QC warehouses found. Please configure QC warehouses in QC Settings."))

    # Convert list to tuple for SQL query
    qc_warehouses_tuple = tuple(selected_warehouses)

    # Fetch stock entry details for QC-related warehouses
    stock_data = frappe.db.sql("""
        SELECT 
            se.name AS stock_entry, 
            se.posting_date, 
            sed.reference_purchase_receipt AS purchase_receipt,
            sed.item_code, 
            item.item_name, 
            item.item_group, 
            sed.t_warehouse AS warehouse, 
            item.stock_uom, 
            sed.transfer_qty,
            sed.custom_qc_done_qty AS qc_done_qty,
            sed.batch_no             
        FROM `tabStock Entry` se
        JOIN `tabStock Entry Detail` sed ON se.name = sed.parent
        JOIN `tabItem` item ON sed.item_code = item.item_code
        WHERE se.docstatus = 1
        AND sed.t_warehouse IN %(qc_warehouses)s
        ORDER BY se.posting_date, sed.item_code
    """, {
        "qc_warehouses": qc_warehouses_tuple,
        "default_qc_processing_warehouse": default_qc_processing_warehouse
    }, as_dict=True)


        # Add button dynamically
    for row in stock_data:
        if row["warehouse"] == default_qc_processing_warehouse:
            item_code = html.escape(row["item_code"] or "")
            batch_no = html.escape(row["batch_no"] or "")
            stock_entry = html.escape(row["stock_entry"] or "")
            transfer_qty = str(row["transfer_qty"]) if row["transfer_qty"] is not None else "0"
            # transfer_qty = html.escape(row["transfer_qty"] or "")

            row["CreateQC"] = f"""
                <button class="btn btn-primary pt-0 pb-0 create_qc" 
                    data-item_code="{html.escape(row["item_code"] or "")}" 
                    data-batch_no="{html.escape(row["batch_no"] or "")}" 
                    data-stock_entry="{html.escape(row["stock_entry"] or "")}" 
                    data-transfer_qty="{row["transfer_qty"] if row["transfer_qty"] is not None else "0"}"
                    style="background-color: grey">
                    Create QC
                </button>
            """
        else:
            row["CreateQC"] = ""

    return stock_data

# onclick="redirectToQCForm('{item_code}', '{batch_no}', '{purchase_receipt}', '{transfer_qty}')"


# row["CreateQC"] = f"""
#     <button class="btn btn-primary pt-0 pb-0 create_qc" 
#         data-item_code="{html.escape(row["item_code"] or "")}" 
#         data-batch_no="{html.escape(row["batch_no"] or "")}" 
#         data-purchase_receipt="{html.escape(row["purchase_receipt"] or "")}" 
#         data-transfer_qty="{row["transfer_qty"] if row["transfer_qty"] is not None else "0"}" 
#         style="background-color: grey">
#         Create QC
#     </button>
# """



# @frappe.whitelist()
# def get_qc_warehouses():
#     """Fetch QC warehouses from QC Settings and return properly formatted data."""
#     qc_warehouses = frappe.db.sql("""
#         SELECT value, '' as description
#         FROM `tabSingles` 
#         WHERE doctype = 'QC Settings' 
#         AND field IN ('default_qc_processing_warehouse', 'default_qc_rejected_warehouse', 'default_rework_warehouse', 'default_return_warehouse')
#     """, as_dict=True)

#     # Return a structured list of dictionaries for MultiSelectList
#     return qc_warehouses







# def get_data(filters):
#     # Fetch QC warehouses from `tabSingles` table
#     qc_warehouses = frappe.db.sql("""
#         SELECT field, value 
#         FROM `tabSingles` 
#         WHERE doctype = 'QC Settings' 
#         AND field IN ('default_qc_processing_warehouse', 'default_qc_rejected_warehouse', 'default_rework_warehouse', 'default_return_warehouse')
#     """, as_dict=True)

#     # Extract warehouse values and filter out None values
#     qc_warehouses_list = [row["value"] for row in qc_warehouses if row["value"]]

#     # Ensure at least one warehouse is found
#     if not qc_warehouses_list:
#         frappe.throw(_("No QC warehouses found. Please configure QC warehouses in QC Settings."))

#     # If user selects warehouses in filter, override default QC warehouses
#     if filters and filters.get("warehouse"):
#         selected_warehouses = filters.get("warehouse")
#     else:
#         selected_warehouses = qc_warehouses_list

#      # Ensure at least one warehouse is found
#     if not selected_warehouses:
#         frappe.throw(_("No QC warehouses found. Please configure QC warehouses in QC Settings."))

#     # Convert list to tuple for SQL query
#     qc_warehouses_tuple = tuple(selected_warehouses)

#     # Fetch stock balances only for QC-related warehouses
#     stock_data = frappe.db.sql("""
#         SELECT 
#             bin.item_code, item.item_name, item.item_group, 
#             bin.warehouse, item.stock_uom, bin.actual_qty AS balance_qty
#         FROM `tabBin` bin
#         JOIN `tabItem` item ON bin.item_code = item.item_code
#         WHERE bin.warehouse IN %(qc_warehouses)s
#         ORDER BY bin.item_code, bin.warehouse
#     """, {"qc_warehouses": qc_warehouses_tuple}, as_dict=True)

#     return stock_data

