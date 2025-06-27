import frappe
from frappe.utils import flt
from frappe import _
from mantra_dev.mantra_dev.report.bom_stock_calculated_with_valuation_rate.bom_stock_calculated_with_valuation_rate import get_stock_data,get_in_transit_qty,get_latest_stock_qty2,get_raw_materials_for_bom,get_warehouse_conditions,create_button
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
            shortage_qty = max(0, material_qty - (stock_data['available_qty'] + stock_data['transit_qty']- get_reserved_qty(material_item_code)))

            row_data = {
                'raw_material_item': material_item_code,
                'item_code': material_item_code,
                item_code: material_qty,
                'available_qty':stock_data['available_qty'],
                'transit_qty':stock_data['transit_qty'],
                'reserve_qty':get_reserved_qty(material_item_code),
                'shortage_qty': shortage_qty,
                'total_qty': material_qty,
                'valuation_rate': valuation_rate * material_qty,
                'create_purchase_order': create_button(
                    "Create Purchase Order", "background-color: gray;", "create-po",
                    {"item_code": material_item_code, "shortage_qty": shortage_qty}
                ) if shortage_qty > 0 else "",
                'create_material_transfer': create_button(
                    "Create Material Transfer", "background-color: gray;", "create-mt",
                    {"item_code": material_item_code, "shortage_qty": shortage_qty}
                ) if shortage_qty > 0 else "",
                'create_work_order' : create_button(
                    "Create Work Order", "background-color: gray", "create-wo",
                    {"item_code": material_item_code, "shortage_qty": shortage_qty}
                ) if shortage_qty > 0 else ""
            }

            existing_row = next((row for row in data if row['raw_material_item'] == material_item_code), None)
            if existing_row:
                existing_row[item_code] = existing_row.get(item_code, 0) + material_qty
                existing_row['total_qty'] += material_qty
                existing_row['valuation_rate'] = valuation_rate * existing_row['total_qty']
                existing_row['shortage_qty'] = max(0, existing_row['total_qty'] - (existing_row['available_qty'] + existing_row['transit_qty']-existing_row['reserve_qty']))
                existing_row['create_purchase_order'] = create_button(
                    "Create Purchase Order", "background-color: gray;", "create-po",
                    {"item_code": material_item_code, "shortage_qty": existing_row['shortage_qty']}
                ) if existing_row['shortage_qty'] > 0 else ""

                existing_row['create_material_transfer'] = create_button(
                    "Create Material Transfer", "background-color: gray;", "create-mt",
                    {"item_code": material_item_code, "shortage_qty": existing_row['shortage_qty']}
                ) if existing_row['shortage_qty'] > 0 else ""
                existing_row['create_work_order'] = create_button(
                    "Create Work Order", "background-color: gray", "create-wo",
                    {"item_code": material_item_code, "shortage_qty": existing_row['shortage_qty']}
                ) if existing_row['shortage_qty'] > 0 else ""
            else:
                data.append(row_data)
    
    return columns, data


def get_reserved_qty(item_code):
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
    reserved_qty = frappe.db.sql(
        f"""
        SELECT SUM(reserved_qty_for_production)
        FROM `tabBin`
        WHERE item_code = %s
        """,
        values,
    )[0][0]
    return reserved_qty or 0


def get_columns(items):
    base_columns = [
        {"fieldname": "raw_material_item", "label": _("Raw Material"), "fieldtype": "Link", "options": "Item", "width": 150},
        {"fieldname": "total_qty", "label": _("Total Required Qty"), "fieldtype": "Float", "width": 150},
        {"fieldname": "available_qty", "label": _("Available Qty"), "fieldtype": "Float", "width": 120},
        {"fieldname": "reserve_qty", "label": _("Reserved Qty"), "fieldtype": "Float", "width": 120},
        {"fieldname": "transit_qty", "label": _("In Transit Qty"), "fieldtype": "Float", "width": 120},
        {"fieldname": "shortage_qty", "label": _("Shortage Qty"), "fieldtype": "Float", "width": 120},
        {"fieldname": "valuation_rate", "label": _("Valuation"), "fieldtype": "Currency", "width": 150},
    ]
    existing_fieldnames = {col["fieldname"] for col in base_columns}
    dynamic_columns = [
        {
            "fieldname": item["item"],
            "label": _(item["item"]),
            "fieldtype": "Float",
            "width": 150,
            "align": "right"
        }
        for item in items if item["item"] not in existing_fieldnames
    ]
    action_columns = [
        {"fieldname": "create_purchase_order", "label": _("Purchase Order"), "fieldtype": "Data", "width": 200},
        {"fieldname": "create_material_transfer", "label": _("Material Transfer"), "fieldtype": "Data", "width": 200},
        {"fieldname": "create_work_order", "label": _("Work Order"), "fieldtype": "Data", "width": 200},
    ]

    return base_columns + dynamic_columns + action_columns
