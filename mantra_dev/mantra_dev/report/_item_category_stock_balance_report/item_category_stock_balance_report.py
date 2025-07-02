import frappe
from frappe import _

def execute(filters=None):
    columns, data = [], []

    # Define columns
    columns = [
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": _("Stock Balance"),
            "fieldname": "stock_balance",
            "fieldtype": "Float",
            "width": 300
        }
    ]

    # Base SQL query
    query = """
        SELECT 
            i.item_code,
            i.item_name AS item_name,
            SUM(b.actual_qty) AS stock_balance
        FROM 
            `tabBin` b
        JOIN 
            `tabItem` i ON b.item_code = i.item_code
        JOIN
            `tabWarehouse` w ON b.warehouse = w.name
        WHERE
            w.custom_is_not_countable = 0
    """
    
    # Add filter condition
    conditions = []
    if filters.get("item_group"):
        conditions.append("i.item_group = %(item_group)s")
    
    if conditions:
        query += " AND ".join(conditions)
    
    # Add group by and order by
    query += """
        GROUP BY 
            i.item_code
        ORDER BY 
            i.item_code
    """

    # Fetch data
    data = frappe.db.sql(query, filters, as_dict=1)

    return columns, data
