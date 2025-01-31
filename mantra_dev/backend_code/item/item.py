import frappe

@frappe.whitelist()
def fetch_item_used_as_raw_material_in_bom(item_code):
    data = frappe.db.sql(
        """
        SELECT 
            bi.parent AS bom,
            b.is_default AS is_default_bom,
            b.item as item_code,
            b.item_name,
            bi.qty,
            bi.uom
        FROM
            `tabBOM Item` AS bi
        LEFT JOIN
            `tabBOM` AS b ON bi.parent = b.name
        WHERE
            bi.docstatus = 1
            AND bi.item_code = %(item_code)s
        GROUP BY
            b.item
        ORDER BY 
            b.is_default DESC, b.item ASC
        """, {"item_code": item_code}, as_dict=True
    )

    return data