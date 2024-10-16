# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Sum
from frappe.utils.data import comma_and
from pypika.terms import ExistsCriterion

def execute(filters=None):
    columns = get_columns()
    data = []

    bom_data = get_bom_data(filters)
    qty_to_make = filters.get("qty_to_make")

    if qty_to_make is None:
        frappe.throw("Quantity to Make is required.")

    manufacture_details = get_manufacturer_records()

    for row in bom_data:
        # Debugging prints
        qty_per_unit = row.qty_per_unit or 0
        required_qty = qty_to_make * qty_per_unit
        # required_qty = required_qty+required_qty1
        last_purchase_rate = frappe.db.get_value("Item", row.item_code, "last_purchase_rate")

        # More debugging output
        print(f"Item Code: {row.item_code}, Qty Per Unit: {qty_per_unit}, Quantity to Make: {qty_to_make}")
        print(f"Calculated Required Qty: {required_qty}")

        data.append(get_report_data(last_purchase_rate, required_qty, row, manufacture_details))

    return columns, data

def get_report_data(last_purchase_rate, required_qty, row, manufacture_details):
    qty_per_unit = row.qty_per_unit if row.qty_per_unit > 0 else 0
    difference_qty = (row.actual_qty or 0) - required_qty
    
    return [
        row.item_code,
        row.description,
        comma_and(manufacture_details.get(row.item_code, {}).get("manufacturer", []), add_quotes=False),
        comma_and(manufacture_details.get(row.item_code, {}).get("manufacturer_part", []), add_quotes=False),
        qty_per_unit,
        row.actual_qty,
        required_qty,
        difference_qty,
        last_purchase_rate,
    ]

def get_columns():
    return [
        {
            "fieldname": "item",
            "label": _("Item"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 120,
        },
        {
            "fieldname": "description",
            "label": _("Description"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "manufacturer",
            "label": _("Manufacturer"),
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "manufacturer_part_number",
            "label": _("Manufacturer Part Number"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "qty_per_unit",
            "label": _("Qty Per Unit"),
            "fieldtype": "Float",
            "width": 110,
        },
        {
            "fieldname": "available_qty",
            "label": _("Available Qty"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "required_qty",
            "label": _("Required Qty"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "difference_qty",
            "label": _("Difference Qty"),
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "fieldname": "last_purchase_rate",
            "label": _("Last Purchase Rate"),
            "fieldtype": "Float",
            "width": 160,
        },
    ]

def get_bom_data(filters):
    # Determine which BOM item table to use based on the exploded view filter
    bom_item_table = "BOM Explosion Item" if filters.get("show_exploded_view") else "BOM Item"

    bom_item = frappe.qb.DocType(bom_item_table)
    bin = frappe.qb.DocType("Bin")

    # Get the list of BOMs from filters
    bom_list = filters.get("bom")
    print("Selected BOM List:", bom_list)

    if not bom_list:
        frappe.throw("Please select at least one BOM.")

    # Ensure the list is properly formatted (e.g., not empty)
    if isinstance(bom_list, str):
        bom_list = [bom_list]

    query = (
        frappe.qb.from_(bom_item)
        .left_join(bin)
        .on(bom_item.item_code == bin.item_code)
        .select(
            bom_item.item_code,
            bom_item.description,
            bom_item.qty_consumed_per_unit.as_("qty_per_unit"),
            IfNull(Sum(bin.actual_qty), 0).as_("actual_qty"),
        )
        .where(
            (bom_item.parent.isin(bom_list)) &
            (bom_item.parenttype == "BOM")
        )
        .groupby(bom_item.item_code)
    )

    # Warehouse filtering
    if filters.get("warehouse"):
        warehouse_details = frappe.db.get_value(
            "Warehouse", filters.get("warehouse"), ["lft", "rgt"], as_dict=True
        )

        if warehouse_details:
            wh = frappe.qb.DocType("Warehouse")
            query = query.where(
                ExistsCriterion(
                    frappe.qb.from_(wh)
                    .select(wh.name)
                    .where(
                        (wh.lft >= warehouse_details.lft)
                        & (wh.rgt <= warehouse_details.rgt)
                        & (bin.warehouse == wh.name)
                    )
                )
            )
        else:
            query = query.where(bin.warehouse == filters.get("warehouse"))

    return query.run(as_dict=True)

def get_manufacturer_records():
    details = frappe.get_all(
        "Item Manufacturer", fields=["manufacturer", "manufacturer_part_no", "item_code"]
    )

    manufacture_details = frappe._dict()
    for detail in details:
        dic = manufacture_details.setdefault(detail.get("item_code"), {})
        dic.setdefault("manufacturer", []).append(detail.get("manufacturer"))
        dic.setdefault("manufacturer_part", []).append(detail.get("manufacturer_part_no"))

    return manufacture_details
