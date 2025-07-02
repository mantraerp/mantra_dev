# # Copyright (c) 2025, Foram Shah and contributors
# # For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	return columns, data




import frappe
from frappe import _
# from apps.erpnext.erpnext.stock.doctype.item.item import Item

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    """Define the columns for the report."""
    return [
         {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Data", "width": 150},
                #  {"label": _("Actual Qty"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 120},

        # {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Purchase Order Date"), "fieldname": "po_date", "fieldtype": "Date", "width": 120},
        {"label": _("Purchase Order"), "fieldname": "po_name", "fieldtype": "Link", "options": "Purchase Order", "width": 250},
         {"label": _("QTY"), "fieldname": "qty", "fieldtype": "float", "width": 120},
        {"label": _("PO Rate"), "fieldname": "rate", "fieldtype": "Currency", "options": "currency", "width": 100},
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 200},
        {"label": _("Quotation"), "fieldname": "supplier_quotation", "fieldtype": "Link", "options": "Supplier Quotation","width": 200},
        {"label": _("Quotation Rate"), "fieldname": "quotation_rate", "fieldtype": "Currency", "options": "currency", "width": 100},
        {"label": _("Reason to select the quotation"), "fieldname": "custom_reason_for_selection", "fieldtype": "Data", "width": 200},


    ]
    

def get_data(filters):
    """Fetch the data based on the filters."""

    conditions = []
    data = []
   
    for item in filters.item:

        # actual_qty = frappe.db.get_value("Bin", {"item_code": item}, "sum(actual_qty)") or 0

        # actual_qty_query = f"""
        #     SELECT SUM(actual_qty) 
        #     FROM `tabBin`
        #     WHERE item_code = '{item}'
        # """.format(item=item),as_dict=False
        # actual_qty = frappe.db.sql(actual_qty_query)


        # actual_qty_html = f'<span style="color:green;font-weight:bold;">{actual_qty}</span>'

        # actual_qty_query = f"""
        #     SELECT SUM(bin.actual_qty) 
        #     FROM `tabBin` bin
        #     JOIN `tabWarehouse` w ON bin.warehouse IN w.name
        #     WHERE bin.item_code = '{item}' AND w.custom_is_not_countable != 1
        # """

        actual_qty_query = f"""
            SELECT SUM(bin.actual_qty) 
            FROM `tabBin` bin
            JOIN `tabWarehouse` w ON bin.warehouse = w.name
            WHERE bin.item_code = '{item}' 
            AND w.custom_is_not_countable != 1
        """


        # actual_qty_query = f"""
        #     SELECT SUM(actual_qty) 
        #     FROM `tabBin`as bin,
        #     JOIN `tabWarehouse` w ON w.name = bin.warehouse
        #     WHERE item_code = '{item}' AND w.custom_is_not_countable != 1
        # """
        actual_qty_result = frappe.db.sql(actual_qty_query)  # Default is as_dict=False

        # Extract the actual qty value (avoid NoneType errors)
        actual_qty = actual_qty_result[0][0] if actual_qty_result and actual_qty_result[0][0] is not None else 0

        # Format actual_qty as green-colored HTML
        actual_qty_html = f'<span style="color:green;font-weight:bold;">{actual_qty}</span>'




        # frappe.throw(item)
        query = f"""
            SELECT 
                1 as indent,
                po.name AS po_name,
                po.supplier_name AS supplier,
                poi.supplier_quotation AS supplier_quotation,
                po.custom_reason_for_selection,
                poi.qty as qty,
                (SELECT 
                    qt_item.rate 
                FROM 
                    `tabSupplier Quotation Item` qt_item
                JOIN 
                    `tabSupplier Quotation` qt ON qt.name = qt_item.parent 
                WHERE 
                    qt.name = poi.supplier_quotation 
                    AND qt_item.item_code = poi.item_code
                    AND qt.docstatus = 1
                LIMIT 1) AS quotation_rate,
                poi.rate AS rate,
                # po.transaction_date AS po_date
                (SELECT
                        DATE(v.creation) AS submission_date
                    FROM `tabVersion` v
                    WHERE v.ref_doctype = 'Purchase Order'
                        AND v.docname = po.name
                        AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][0]')) = 'docstatus'
                        AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][1]')) = '0'
                        AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][2]')) = '1'
                    LIMIT 1
                    
                    ) AS po_date
            FROM 
                `tabPurchase Order Item` poi
            JOIN 
                `tabPurchase Order` po ON po.name = poi.parent
           
            WHERE poi.item_code = '{item}'
            AND po.docstatus!= 2
            GROUP BY 
                po.name, poi.item_code
            ORDER BY 
                poi.item_code, po.transaction_date DESC
            LIMIT 10
            """.format(item=item)

        sql_data = frappe.db.sql(query,filters,  as_dict=True)
        if sql_data:
            data.append({"item_code": item, "qty": actual_qty_html, "indent": 0})  # Add actual_qty row

            # data.append({"item_code": item, "indent": 0})
            data += sql_data
    return data


    # query = fquery = f"""
    # SELECT 
    #     po.name AS po_name,
    #     poi.item_code,
    #     poi.item_name,
    #     po.supplier_name AS supplier,
    #     poi.supplier_quotation AS supplier_quotation,
    #     po.custom_reason_for_selection,
    #     (SELECT 
    #         qt_item.rate 
    #      FROM 
    #         `tabSupplier Quotation Item` qt_item
    #      JOIN 
    #         `tabSupplier Quotation` qt ON qt.name = qt_item.parent 
    #      WHERE 
    #         qt.name = poi.supplier_quotation 
    #         AND qt_item.item_code = poi.item_code
    #         AND qt.docstatus = 1
    #      LIMIT 1) AS quotation_rate,
    #     poi.rate AS rate,
    #     # po.transaction_date AS po_date
    #     (SELECT
    #             DATE(v.creation) AS submission_date
    #         FROM `tabVersion` v
    #         WHERE v.ref_doctype = 'Purchase Order'
    #             AND v.docname = po.name
    #             AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][0]')) = 'docstatus'
    #             AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][1]')) = '0'
    #             AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][2]')) = '1'
    #         LIMIT 1
            
    #         ) AS po_date
    # FROM 
    #     `tabPurchase Order Item` poi
    # JOIN 
    #     `tabPurchase Order` po ON po.name = poi.parent
    # {where_clause}
    # AND po.docstatus!= 2
    # GROUP BY 
    #     po.name, poi.item_code
    # ORDER BY 
    #     poi.item_code, po.transaction_date DESC
    # LIMIT 50
    # """


    

    # return frappe.db.sql(query,filters,  as_dict=True)


    








# import frappe
# from frappe import _

# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data

# def get_columns():
#     """Define the columns for the report."""
#     return [
#         {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Data", "width": 150},
#         {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
#         {"label": _("Purchase Order Date"), "fieldname": "po_date", "fieldtype": "Date", "width": 120},
#         {"label": _("Purchase Order"), "fieldname": "po_name", "fieldtype": "Link", "options": "Purchase Order", "width": 250},
#         {"label": _("PO Rate"), "fieldname": "rate", "fieldtype": "Currency", "options": "currency", "width": 100},
#         {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 200},
#         {"label": _("Quotation"), "fieldname": "supplier_quotation", "fieldtype": "Link", "options": "Supplier Quotation", "width": 200},
#         {"label": _("Quotation Rate"), "fieldname": "quotation_rate", "fieldtype": "Currency", "options": "currency", "width": 100},
#         {"label": _("Reason to select the quotation"), "fieldname": "custom_reason_for_selection", "fieldtype": "Data", "width": 200},
#     ]

# def get_data(filters):
#     """Fetch the data and structure it."""
#     conditions = []
#     query_params = {}

#     if filters.get("item"):
#         item_codes = filters.get("item")  
#         if isinstance(item_codes, str):  # Convert string (JSON format) to list
#             item_list = frappe.parse_json(item_codes)
#         elif isinstance(item_codes, int):  # Convert single int to list
#             item_list = [item_codes]
#         else:
#             item_list = item_codes  # Already a list
        
#         if item_list:
#             conditions.append("poi.item_code IN %(items)s")
#             query_params["items"] = tuple(item_list)

#     where_clause = " AND ".join(conditions)
#     where_clause = f"WHERE {where_clause}" if where_clause else ""

#     # **Fixed Query Without Duplicate POs**
#     query = f"""
#     WITH RankedOrders AS (
#         SELECT 
#             poi.item_code,
#             poi.item_name,
#             po.name AS po_name,
#             po.supplier_name AS supplier,
#             poi.supplier_quotation AS supplier_quotation,
#             po.custom_reason_for_selection,
#             (SELECT qt_item.rate 
#              FROM `tabSupplier Quotation Item` qt_item
#              JOIN `tabSupplier Quotation` qt ON qt.name = qt_item.parent 
#              WHERE qt.name = poi.supplier_quotation 
#                AND qt_item.item_code = poi.item_code
#                AND qt.docstatus = 1
#              LIMIT 1) AS quotation_rate,
#             poi.rate AS rate,
#             (SELECT DATE(v.creation)
#              FROM `tabVersion` v
#              WHERE v.ref_doctype = 'Purchase Order'
#                AND v.docname = po.name
#                AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][0]')) = 'docstatus'
#                AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][1]')) = '0'
#                AND JSON_UNQUOTE(JSON_EXTRACT(v.data, '$.changed[2][2]')) = '1'
#              LIMIT 1) AS po_date,
#             ROW_NUMBER() OVER (PARTITION BY poi.item_code ORDER BY po.transaction_date DESC) AS row_num
#         FROM 
#             `tabPurchase Order Item` poi
#         JOIN 
#             `tabPurchase Order` po ON po.name = poi.parent
#         {where_clause}
#         AND po.docstatus != 2
#     )
#     SELECT 
#         item_code, 
#         item_name, 
#         po_date, 
#         po_name, 
#         rate, 
#         supplier, 
#         supplier_quotation, 
#         quotation_rate, 
#         custom_reason_for_selection,
#         1 as indent
#     FROM RankedOrders 
#     WHERE row_num <= 10
#     GROUP BY item_code, po_name
#     ORDER BY item_code, po_date DESC;
#     """

#     return frappe.db.sql(query, query_params, as_dict=True)
