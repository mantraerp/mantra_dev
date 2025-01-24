// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["GRN Bill Remain"] = {
	"filters": [
		{
			fieldname: "remove_created_bill",
			label: __("Remove 100% bill created"),
			fieldtype: "Check",
			default: 1,
		},
		{
			fieldname: "remove_service_items",
			label: __("Remove service item"),
			fieldtype: "Check",
			default: 1,
		},
		{
			fieldname: "new_to_old",
			label: __("New to Old"),
			fieldtype: "Check",
			default: 0,
		}
	]
};
