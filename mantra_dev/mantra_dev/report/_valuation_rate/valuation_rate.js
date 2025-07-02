// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Valuation Rate"] = {
	"filters": [
		{
            "fieldname": "item_code",
            "label": __("Item Code"),
            "fieldtype": "MultiSelectList",
			"options": "Item",
			get_data: function (txt) {
				return frappe.db.get_link_options("Item", txt);
			},
        },
		{
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "MultiSelectList",
			"options": "Warehouse",
			get_data: function (txt) {
				return frappe.db.get_link_options("Warehouse", txt);
			},
        },
	]
};
