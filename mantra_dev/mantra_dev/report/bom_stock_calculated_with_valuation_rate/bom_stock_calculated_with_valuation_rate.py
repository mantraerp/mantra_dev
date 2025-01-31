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
    warehouses = filters.get("warehouse")
    warehouse_list = frappe.parse_json(warehouses) if warehouses else []
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
                bom_qty = frappe.db.get_value("BOM", material.get('parent'), 'quantity') or 1
                material_qty = round((flt(material.get('qty'), 2) / flt(bom_qty, 2)) * qty, 2)
              # Determine warehouse condition
                if warehouse_list:
                    if len(warehouse_list) > 1:
                        warehouse_condition = "AND warehouse IN ({})".format(", ".join(["%s"] * len(warehouse_list)))
                        args = (material_item_code,) + tuple(warehouse_list)  # Pass tuple for multiple warehouses
                    else:
                        warehouse_condition = "AND warehouse = %s"
                        args = (material_item_code, warehouse_list[0])  # Pass single warehouse
                else:
                    warehouse_condition = ""  # No warehouse filter
                    args = (material_item_code,)  # Only material_item_code is passed if no warehouse filter
                ready_stock = get_stock_qty_by_category(material_item_code, "Ready Stock", warehouse_list)
                faulty_stock = get_stock_qty_by_category(material_item_code, "Faulty", warehouse_list)
                qc_stock = get_stock_qty_by_category(material_item_code, "QC", warehouse_list)
                actual_qty = get_latest_stock_qty2(material_item_code, warehouse_list)
                # Execute the SQL query
                valuation_rate = frappe.db.sql(
                    """
                    SELECT SUM(stock_value_difference) / SUM(actual_qty)
                    FROM `tabStock Ledger Entry`
                    WHERE item_code = %s
                    {warehouse_condition}
                    AND is_cancelled = 0
                    """.format(warehouse_condition=warehouse_condition),
                    args,
                )[0][0] or 0
                transit_qty = get_in_transit_qty(material_item_code, from_date)
                shortage_qty = actual_qty + transit_qty - material_qty
                if shortage_qty > 0:
                    shortage_qty = 0
                else:
                    shortage_qty = abs(shortage_qty)
                row_data = {
                        'raw_material_item': material_item_code,
                        'item_code': material_item_code,  
                        item_code: material_qty,  
                        'available_qty': actual_qty if actual_qty  else 0,
                        'transit_qty': transit_qty,
                        'shortage_qty': shortage_qty,
                        'ready_stock': ready_stock,
                        'faulty': faulty_stock,
                        'qc': qc_stock
                    }
                total_qty = sum([value for key, value in row_data.items() if key not in  ['raw_material_item','valuation_rate','item_code','available_qty','transit_qty','shortage_qty','qc','ready_stock','faulty'] and isinstance(value, (int, float))])
               
                row_data['total_qty'] = total_qty
                row_data['valuation_rate'] = valuation_rate * total_qty
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
                    existing_row['shortage_qty'] = existing_row['available_qty'] + existing_row['transit_qty'] - existing_row['total_qty']
                    if existing_row['shortage_qty'] > 0:
                        existing_row['shortage_qty'] = 0  
                    else:
                        existing_row['shortage_qty'] = abs(existing_row['shortage_qty'])
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
            "label": _("Valuation Rate"),
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

