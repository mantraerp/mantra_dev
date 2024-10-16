# Path: [your_module]/report/SalesInvoiceByCostCenter/SalesInvoiceByCostCenter.py
import frappe
from frappe import _

def execute(filters=None):
    columns, data = [], []
    
    cost_centers = get_cost_centers()
    columns = get_columns(cost_centers)
    data = get_data(cost_centers, filters)
    
    # Add the total row
    data = add_total_row(data, cost_centers)
    
    return columns, data

def get_cost_centers():
    # Fetch all unique cost centers from Sales Invoice
    return [d[0] for d in frappe.db.sql("SELECT DISTINCT cost_center FROM `tabSales Invoice Item`")]

def get_columns(cost_centers):
    # Define columns for the report
    columns = [
        {"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Link", "options": "Sales Person", "width": 150},
    ]
    
    for cc in cost_centers:
        columns.append({"label": _(cc), "fieldname": frappe.scrub(cc), "fieldtype": "Currency", "width": 150})
    
    # Add a total column
    columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 150})
    
    return columns

def get_data(cost_centers, filters):
    # Build dynamic SQL query to pivot data
    pivot_case_statements = ", ".join([f"SUM(CASE WHEN sii.cost_center = '{cc}' THEN sii.base_net_amount ELSE 0 END) as `{frappe.scrub(cc)}`" for cc in cost_centers])
    
    conditions = ["si.docstatus = 1"]
    if filters.get('sales_person'):
        conditions.append("si.custom_sales_person = %(sales_person)s")
    if filters.get('from_date') and filters.get('to_date'):
        conditions.append("si.posting_date BETWEEN %(from_date)s AND %(to_date)s")
    
    conditions = " AND ".join(conditions)
    
    query = f"""
        SELECT
            si.custom_sales_person as sales_person,
            {pivot_case_statements}
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE
            {conditions}
        GROUP BY
            si.custom_sales_person
        ORDER BY
            si.custom_sales_person
    """
    
    data = frappe.db.sql(query, filters, as_dict=1)
    
    # Calculate row-wise total for each sales person
    for row in data:
        row['total'] = sum(row[frappe.scrub(cc)] for cc in cost_centers)
    
    return data

def add_total_row(data, cost_centers):
    # Initialize the total row dictionary
    total_row = {
        'sales_person': 'Total',
        'total': 0
    }
    
    # Initialize cost center totals
    for cc in cost_centers:
        total_row[frappe.scrub(cc)] = 0
    
    # Sum up each column for the total row
    for row in data:
        for cc in cost_centers:
            total_row[frappe.scrub(cc)] += row[frappe.scrub(cc)]
        total_row['total'] += row['total']
    
    # Append the total row to the data
    data.append(total_row)
    
    return data
