# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class QCSettings(Document):
	pass


@frappe.whitelist()
def get_quality_managers(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name FROM `tabUser`
        WHERE name IN (
            SELECT parent FROM `tabHas Role`
            WHERE role = 'Quality Manager'
        ) AND enabled = 1
        AND name LIKE %s
        LIMIT %s, %s
    """, ("%" + txt + "%", start, page_len))
