# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    
    columns = [
        
        {
            "label": _("Sales Area"),
            "fieldname": "sales_area",
            "fieldtype": "Data",
            "width": 170,
        },
        {
            "label": _("Total Sales"),
            "fieldname": "total_sales",
            "fieldtype": "Data",
            "width": 200,
        },
         {
            "label": _("April"),
            "fieldname": "April",
            "fieldtype": "Data",
            "width": 170,
        }, {
            "label": _("May"),
            "fieldname": "May",
            "fieldtype": "Data",
            "width": 170,
        },
         {
            "label": _("June"),
            "fieldname": "June",
            "fieldtype": "Data",
            "width": 170,
        },
         {
            "label": _("July"),
            "fieldname": "July",
            "fieldtype": "Data",
            "width": 170,
        },
         {
            "label": _("August"),
            "fieldname": "August",
            "fieldtype": "Data",
            "width": 170,
        },
         {
            "label": _("September"),
            "fieldname": "September",
            "fieldtype": "Data",
            "width": 170,
        },
         {
            "label": _("October"),
            "fieldname": "October",
            "fieldtype": "Data",
            "width": 170,
        },
         {
            "label": _("November"),
            "fieldname": "November",
            "fieldtype": "Data",
            "width": 170,
        },
           {
            "label": _("December"),
            "fieldname": "December",
            "fieldtype": "Data",
            "width": 170,
        },
       {
            "label": _("January"),
            "fieldname": "January",
            "fieldtype": "Data",
            "width": 170,
        },
          {
            "label": _("February"),
            "fieldname": "February",
            "fieldtype": "Data",
            "width": 170,
        },
         {
            "label": _("March"),
            "fieldname": "March",
            "fieldtype": "Data",
            "width": 170,
        },
  
	]
    
    

    
    
    query = """
        WITH RECURSIVE SalesHierarchy AS (
            SELECT
                name,
                name AS root_sales_person,
                1 AS level
            FROM
                `tabSales Person`
            WHERE
                parent_sales_person = 'Mantra Softech India Private Limited'
            UNION ALL
            SELECT
                sp.name,
                sh.root_sales_person,
                sh.level + 1
            FROM
                `tabSales Person` AS sp
            INNER JOIN
                SalesHierarchy AS sh ON sp.parent_sales_person = sh.name
        ),
        FiscalMonths AS (
            SELECT 1 AS month_number, 'April' AS month_name
            UNION SELECT 2, 'May'
            UNION SELECT 3, 'June'
            UNION SELECT 4, 'July'
            UNION SELECT 5, 'August'
            UNION SELECT 6, 'September'
            UNION SELECT 7, 'October'
            UNION SELECT 8, 'November'
            UNION SELECT 9, 'December'
            UNION SELECT 10, 'January'
            UNION SELECT 11, 'February'
            UNION SELECT 12, 'March'
        )
        SELECT
            COALESCE(SH.root_sales_person, 'Total') AS "sales_area",
            SUM(CASE WHEN MONTH(si.posting_date) = 1 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "January",
            SUM(CASE WHEN MONTH(si.posting_date) = 2 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "February",
            SUM(CASE WHEN MONTH(si.posting_date) = 3 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "March",
            SUM(CASE WHEN MONTH(si.posting_date) = 4 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "April",
            SUM(CASE WHEN MONTH(si.posting_date) = 5 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "May",
            SUM(CASE WHEN MONTH(si.posting_date) = 6 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "June",
            SUM(CASE WHEN MONTH(si.posting_date) = 7 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "July",
            SUM(CASE WHEN MONTH(si.posting_date) = 8 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "August",
            SUM(CASE WHEN MONTH(si.posting_date) = 9 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "September",
            SUM(CASE WHEN MONTH(si.posting_date) = 10 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "October",
            SUM(CASE WHEN MONTH(si.posting_date) = 11 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "November",
            SUM(CASE WHEN MONTH(si.posting_date) = 12 THEN COALESCE(si.base_total, 0) ELSE 0 END) AS "December",
            SUM(COALESCE(si.base_total, 0)) AS "total_sales"
        FROM
            SalesHierarchy AS SH
        LEFT JOIN
            `tabSales Invoice` AS si ON si.custom_sales_person = SH.name
       
            
      
    """

    # If filters for date range are provided, add them to the query
    if filters.get("from_date") and filters.get("to_date"):
        query += " AND DATE(si.posting_date) BETWEEN %(from_date)s AND %(to_date)s"
        
    query+="""
        AND si.docstatus=1
		  GROUP BY
            SH.root_sales_person
        ORDER BY
            "sales_area";
	
 		"""
   
   
    # Execute the SQL query
    data = frappe.db.sql(query, filters, as_dict=True)
    
    
    return columns,data
