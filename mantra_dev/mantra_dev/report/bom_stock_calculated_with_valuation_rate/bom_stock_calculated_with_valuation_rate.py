# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Sum
from frappe.utils.data import comma_and
from frappe.utils import flt


def execute(filters=None):
    data = []
    columns = []
    route_data = frappe.parse_json(filters.get("route_data", "[]"))
    warehouse_list = frappe.parse_json(filters.get("warehouse", "[]"))
    from_date = filters.get("from_date")

    if not route_data:
        return columns, data

    columns = get_columns(route_data)
    
    for item_data in route_data:
        item_code, bom_code, qty = item_data.get('item'), item_data.get('bom'), item_data.get('qty')
        
        if bom_code:
            bom_exists = frappe.db.exists("BOM", bom_code)
            if not bom_exists:
                continue
            
        materials = get_raw_materials_for_bom(bom_code) if bom_code else [{'item_code': item_code, 'qty': qty, 'parent': None}]

        for material in materials:
            material_item_code = material.get('item_code')
            bom_qty = frappe.db.get_value("BOM", material.get('parent'), 'quantity') or 1
            material_qty = round((flt(material.get('qty'), 2) / flt(bom_qty, 2)) * qty, 2) if bom_code else qty
            
            warehouse_condition, args = get_warehouse_conditions(material_item_code, warehouse_list)
            valuation_rate = frappe.db.sql(
                """
                SELECT SUM(stock_value_difference) / SUM(actual_qty)
                FROM `tabStock Ledger Entry`
                WHERE item_code = %s {warehouse_condition} AND is_cancelled = 0
                """.format(warehouse_condition=warehouse_condition), args
            )[0][0] or 0

            stock_data = get_stock_data(material_item_code, warehouse_list, from_date)
            shortage_qty = max(0, material_qty - (stock_data['available_qty'] + stock_data['transit_qty']))

            row_data = {
                'raw_material_item': material_item_code,
                'item_code': material_item_code,
                item_code: material_qty,
                **stock_data,
                'shortage_qty': shortage_qty,
                'total_qty': material_qty,
                'valuation_rate': valuation_rate * material_qty
            }

            existing_row = next((row for row in data if row['raw_material_item'] == material_item_code), None)
            if existing_row:
                existing_row[item_code] = existing_row.get(item_code, 0) + material_qty
                existing_row['total_qty'] += material_qty
                existing_row['valuation_rate'] = valuation_rate * existing_row['total_qty']
                existing_row['shortage_qty'] = max(0, existing_row['total_qty'] - (existing_row['available_qty'] + existing_row['transit_qty']))
            else:
                data.append(row_data)
    
    return columns, data

def get_warehouse_conditions(item_code, warehouse_list):
    if warehouse_list:
        warehouse_condition = "AND warehouse IN ({})".format(", ".join(["%s"] * len(warehouse_list)))
        args = (item_code,) + tuple(warehouse_list)
    else:
        warehouse_condition, args = "", (item_code,)
    return warehouse_condition, args

def get_stock_data(item_code, warehouse_list, from_date):
    return {
        'available_qty': get_latest_stock_qty2(item_code, warehouse_list) or 0,
        'transit_qty': get_in_transit_qty(item_code, from_date),
        'ready_stock': get_stock_qty_by_category(item_code, "Ready Stock", warehouse_list),
        'faulty': get_stock_qty_by_category(item_code, "Faulty", warehouse_list),
        'qc': get_stock_qty_by_category(item_code, "QC", warehouse_list)
    }


def get_in_transit_qty(item_code, date_filter=None):
    """
    Fetches the total expected quantity for a specific item based on the Purchase Order 
    and the Final Expected Receive Date.

    Parameters:
    - item_code (str): The code of the item for which the in-transit quantity is to be fetched.
    - date_filter (str, optional): The date to filter the Final Expected Receive Date. 
      If not provided, defaults to today's date.

    Returns:
    - in_transit_qty (float): The total in-transit quantity for the item.
    """
    # Use the provided date_filter, or default to today's date if not provided
    if not date_filter:
        date_filter = frappe.utils.getdate()  # This will give today's date
    
    in_transit_qty = frappe.db.sql("""
        SELECT SUM(expected_qty)
        FROM `tabPurchase Order Expected Date` as poed
        WHERE poed.item_code = %s
        AND poed.status = 'Approved'  
        AND poed.final_expected_receive_date <= %s  
    """, (item_code, date_filter))[0][0] or 0
    
    return in_transit_qty

def get_latest_stock_qty2(item_code, warehouses=None):
    """
    Fetches the latest stock quantity of a specific item in a specific warehouse (if provided).
    This function queries the `tabBin` table in the database to get the sum of the `actual_qty` 
    for the given item code.

    Parameters:
    - item_code (str): The code of the item for which the stock quantity is to be fetched.
    - warehouse (str, optional): The warehouse to filter the stock quantity. If not provided, 
      the total stock across all warehouses is returned.

    Returns:
    - actual_qty (float): The total stock quantity for the item. If no stock is found, 
      it returns `None`.
    """
    values = [item_code]
    condition = ""
    if warehouses:
        condition = "AND warehouse IN %s"
        values.append(tuple(warehouses))
    else:
        condition = "AND warehouse IN (SELECT name FROM `tabWarehouse` WHERE custom_is_not_countable = 1)"
    actual_qty = frappe.db.sql(
        f"""
        SELECT SUM(actual_qty) 
        FROM `tabBin`
        WHERE item_code = %s {condition}
        """,
        values,
    )[0][0]
    return actual_qty or 0


def get_raw_materials_for_bom(bom_code):
    """ Fetches the raw materials for a given BOM. """
    raw_materials = []
    bom_items = frappe.get_all('BOM Item', filters={'parent': bom_code}, fields=['item_code', 'qty','parent'])
    for bom_item in bom_items:
        raw_materials.append(bom_item)
    
    return raw_materials

def get_columns(items):
    columns=[
        {
            "fieldname": "raw_material_item",
            "label": _("Raw Material"),
            "fieldtype": "Link",
            "options":"Item",
            "width": 150
        },
        {
            "fieldname": "total_qty",
            "label": _("Total Required Qty"),
            "fieldtype": "float",
            "width": 150
        },
        {
            "fieldname": "available_qty",
            "label": _("Available Qty"),
            "fieldtype": "float",
            "width": 120,
        },
        {
            "fieldname": "ready_stock",
            "label": _("Ready Stock"),
            "fieldtype": "float",
            "width": 120,
        },
        {
            "fieldname": "faulty",
            "label": _("Faulty"),
            "fieldtype": "float",
            "width": 120,
        },
        {
            "fieldname": "qc",
            "label": _("QC"),
            "fieldtype": "float",
            "width": 120,
        },
        {
            "fieldname": "transit_qty",
            "label": _("In Transit Qty"),
            "fieldtype": "float",
            "width": 120,
        },
        {
            "fieldname": "shortage_qty",
            "label": _("Shortage Qty"),
            "fieldtype": "float",
            "width": 120,
        },
        {
            "fieldname": "valuation_rate",
            "label": _("Valuation"),
            "fieldtype": "Currency",
            "width": 150
        },
      
    ]
    for item in items:
        item_name = item.get("item")
        if not any(column['fieldname'] == item_name for column in columns):
            columns.append({
                "fieldname": item_name,
                "label": _(f"{item_name}"),
                "fieldtype": "Float",
                "width": 150,
                "align":"right"
            })
    return columns



def get_stock_qty_by_category(item_code, category, warehouses=None):
    """
    Fetch stock quantity from warehouses based on the given category and selected warehouse filter.

    Parameters:
    - item_code (str): The item code for which stock is required.
    - category (str): The warehouse category to filter (e.g., 'Ready Stock', 'Faulty', 'QC').
    - warehouses (list, optional): A list of warehouses to filter stock from.

    Returns:
    - float: The total stock quantity based on the category and warehouse filter.
    """
    values = [item_code, category]
    condition = "AND warehouse IN (SELECT name FROM `tabWarehouse` WHERE custom_category = %s)"
    
    if warehouses:
        condition += " AND warehouse IN %s"
        values.append(tuple(warehouses))
    
    return frappe.db.sql(f"""
        SELECT SUM(actual_qty)
        FROM `tabBin`
        WHERE item_code = %s {condition}
    """, values)[0][0] or 0

