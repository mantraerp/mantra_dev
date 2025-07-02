// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Balance by Item Category and Warehouse"] = {
    "filters": [
        {
            "fieldname": "item_category",
            "label": __("Item Category"),
            "fieldtype": "Link",
            "options": "Item Group",
            "default": "",
            "reqd": 0
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "default": "",
            "reqd": 0
        }
    ]
};
