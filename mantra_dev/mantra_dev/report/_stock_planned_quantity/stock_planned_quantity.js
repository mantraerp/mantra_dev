// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Planned Quantity"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": __("Date"),
            "fieldtype": "Date"
        },
    ],
};