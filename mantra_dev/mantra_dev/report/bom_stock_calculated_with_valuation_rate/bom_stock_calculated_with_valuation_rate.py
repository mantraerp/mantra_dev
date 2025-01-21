# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Sum
from frappe.utils.data import comma_and
from frappe.utils import flt

def execute(filters=None):
    """
    This function generates a report based on the provided filters, primarily focusing on raw materials required 
    for specific items (as per their BOM - Bill of Materials) and the stock availability and valuation rates in a 
    specific warehouse.

    Parameters:
    - filters (dict): A dictionary containing filter options, specifically:
        - route_data: A JSON string representing the selected items, their BOM, and required quantities.
        - warehouse: The name of the warehouse to fetch stock information from.

    Returns:
    - columns (list): A list of columns for the report, dynamically generated based on the selected items.
    - data (list): A list of dictionaries containing details of raw materials, their required quantities, 
      stock availability, and valuation rates.

    Key Steps:
    1. Extracts the route data and warehouse information from the filters.
    2. Parses the `route_data` to retrieve item details such as item code, BOM, and required quantity.
    3. For each item, fetches the raw materials required based on the BOM and calculates the total quantity 
       required for each raw material.
    4. Fetches the latest stock quantity and valuation rate for each raw material from the database.
    5. Aggregates the raw material data (e.g., quantities required for multiple items) into a consolidated row.
    6. Appends the consolidated data to the report.

    Detailed Explanation:
    - `get_columns(selected_items)`: Dynamically generates the columns for the report based on the selected items.
    - `get_raw_materials_for_bom(bom_code)`: Retrieves the list of raw materials and their quantities for a specific BOM.
    - `get_latest_stock_qty2(material_item_code, warehouse)`: Fetches the latest stock quantity for a raw material 
       in the specified warehouse.
    - SQL-like query (via Frappe Query Builder):
        - Calculates the latest valuation rate for a raw material based on its stock ledger entries.
        - Filters out cancelled entries and optionally filters by warehouse.

    Row Data Fields:
    - 'raw_material_item': The code of the raw material.
    - 'item_code': The code of the raw material (redundant for now).
    - '<item_code>': The quantity of the raw material required for a specific item.
    - 'qty': The total quantity of the raw material required.
    - 'valuation_rate': The latest valuation rate of the raw material.
    - 'available_qty': The available stock quantity of the raw material in the specified warehouse.
    - 'total_qty': The total quantity required across all items.

    Additional Features:
    - Avoids duplication: Consolidates data for raw materials already present in the report.
    - Dynamically updates existing rows if new quantities are added.
    """
    data=[]
    columns=[]
    route_data = filters.get("route_data")
    warehouse = filters.get("warehouse")
    from_date = filters.get("from_date") 
    if route_data:
        selected_items = frappe.parse_json(route_data)
        columns = get_columns(selected_items)
        for item_data in selected_items:
            item_code = item_data.get('item')
            bom_code = item_data.get('bom')
            qty = item_data.get('qty')
            raw_materials = get_raw_materials_for_bom(bom_code)
            row_data={}
            total_qty = 0
            for material in raw_materials:
                material_item_code = material.get('item_code')
                material_qty = material.get('qty') * qty
                actual_qty = get_latest_stock_qty2(material_item_code, warehouse)
                table = frappe.qb.DocType("Stock Ledger Entry")
                query = (
                    frappe.qb.from_(table)
                    .select(Sum(table.stock_value_difference) / Sum(table.actual_qty))
                    .where(
                        (table.item_code == material_item_code)
                        & (table.is_cancelled == 0)
                    )
                )
                if warehouse:
                    query = query.where(table.warehouse == warehouse) 
                last_valuation_rate = query.run()
                valuation_rate = (
                    last_valuation_rate[0][0]
                    if last_valuation_rate and last_valuation_rate[0][0] not in [None, 'null']
                    else 0.0
                )
                transit_qty = get_in_transit_qty(material_item_code, from_date)
                row_data = {
                        'raw_material_item': material_item_code,
                        'item_code': material_item_code,  
                        item_code: material_qty,  
                        'qty': material_qty, 
                        'valuation_rate':valuation_rate * total_qty,
                        'available_qty': actual_qty if actual_qty  else 0,
                        'transit_qty': transit_qty
                    }
                total_qty = sum([value for key, value in row_data.items() if key not in  ['raw_material_item','valuation_rate','qty','item_code','available_qty'] and isinstance(value, (int, float))])
                row_data['total_qty'] = total_qty
                existing_row = None
                if len(data) > 1:
                    existing_row = next((row for row in data if row['raw_material_item'] == material_item_code), None)
                if existing_row:
                    if item_code in existing_row:
                        existing_row[item_code] += material_qty
                    else:
                        existing_row[item_code] = material_qty 
                    existing_row['total_qty'] += material_qty
                    existing_row['valuation_rate'] = valuation_rate * existing_row['total_qty']
                    existing_row['transit_qty'] = transit_qty
                else:
                    data.append(row_data)
    return columns, data


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

def get_latest_stock_qty2(item_code, warehouse=None):
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
    if warehouse:
        condition = f"AND warehouse = %s"
        values.append(warehouse)
    actual_qty = frappe.db.sql(
        f"""select sum(actual_qty) from tabBin
        where item_code=%s {condition}""",
        values,
    )[0][0]
    return actual_qty


def get_raw_materials_for_bom(bom_code):
    """ Fetches the raw materials for a given BOM. """
    raw_materials = []
    bom_items = frappe.get_all('BOM Item', filters={'parent': bom_code}, fields=['item_code', 'qty'])
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
            "label": _("Total Qty"),
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
            "fieldname": "valuation_rate",
            "label": _("Valuation Rate"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "transit_qty",
            "label": _("In Transit Qty"),
            "fieldtype": "float",
            "width": 120,
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


