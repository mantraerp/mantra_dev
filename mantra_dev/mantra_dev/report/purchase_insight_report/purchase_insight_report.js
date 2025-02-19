// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

// frappe.query_reports["Purchase Insight Report"] = {
// 	"filters": [
// 		{
//             "fieldname": "item",
//             "label": __("Item"),
//             "fieldtype": "Link",
//             "options": "Item",
//             "reqd": 1
//         },

// 	]
// };


frappe.query_reports["Purchase Insight Report"] = {
	"filters": [
		{
            "fieldname": "item",
            "label": __("Item"),
            "fieldtype": "MultiSelectList",
            "options": "Item",
            "get_data": function(txt) {
                return frappe.db.get_link_options("Item", txt);
            }
        }
	],
    "formatter": function (value, row, column, data, default_formatter) {
        // Bold the Main Material Request Row Text Bold
        value = default_formatter(value, row, column, data);
        if (data && data["indent"] === 0) {
			value = `<strong>${value}</strong>`;
		}
        return value;
    }
};


// frappe.query_reports["Purchase Insight Report"].formatter = function(value, row, column, data, default_formatter) {
//     value = default_formatter(value, row, column, data);

//     if (column.fieldname === "po_name") {
//         value = `<b>${data.item_code}:</b> ${value}`;
//     }

//     return value;
// };
