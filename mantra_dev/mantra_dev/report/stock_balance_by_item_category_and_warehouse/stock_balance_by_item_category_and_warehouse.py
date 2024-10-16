import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Data", "width": 300},
        {"label": "Item Category", "fieldname": "item_category", "fieldtype": "Data", "width": 300},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 300},
        {"label": "Stock Balance", "fieldname": "stock_balance", "fieldtype": "Float", "width": 300},
    ]

def get_data(filters):
    conditions = []
    if filters.get("item_category"):
        conditions.append("i.item_group = %(item_category)s")
    if filters.get("warehouse"):
        conditions.append("w.name = %(warehouse)s")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
    SELECT 
        i.item_code,
        i.item_group AS item_category,
        w.warehouse_name AS warehouse,
        SUM(b.actual_qty) AS stock_balance
    FROM 
        `tabBin` b
    JOIN 
        `tabItem` i ON b.item_code = i.item_code
    JOIN 
        `tabWarehouse` w ON b.warehouse = w.name
    WHERE 
        {where_clause}
    GROUP BY 
        i.item_code, w.warehouse_name, i.item_group
"""

    data = frappe.db.sql(query, filters, as_dict=True)
    return data
