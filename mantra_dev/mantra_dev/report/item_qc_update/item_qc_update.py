# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data

import frappe

def execute(filters=None):
    columns = [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 180},
        {"label": "UOM", "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 100},
        {"label": "QC Template", "fieldname": "quality_inspection_template", "fieldtype": "Link","options":"Quality Inspection Template" ,"width": 180},
        #  {"label": "Inspection Required", "fieldname": "custom_inspection_required_before_transfer_warehouse", "fieldtype": "Check","width": 180},
        {"label": "Action", "fieldname": "update_button", "fieldtype": "HTML", "width": 130},
    ]

    data = frappe.get_all("Item", fields=["name as item_code", "item_name", "stock_uom","quality_inspection_template"])

    for row in data:
        row["update_button"] = f"""
    <div style='margin-top: 10px; height: 0px; display: flex; align-items: center;'>
        <button class='btn btn-sm btn-primary update-qc' data-item="{row['item_code']}">Update</button>
    </div>
"""
    return columns, data


@frappe.whitelist()
def update_qc_template(item_code, template=None, inspection_required=0):
    frappe.db.set_value("Item", item_code, {
        "quality_inspection_template": template,
        "custom_inspection_required_before_transfer_warehouse": inspection_required
    })
    frappe.db.commit()
