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
		},
		{
            fieldname: "po_created_user",
            label: __("PO Created By"),
            fieldtype: "Select",
            reqd: 0,
            options: []
        }
	],
	onload: function(report){
        frappe.call({
            method: "mantra_dev.mantra_dev.report.grn_bill_remain.grn_bill_remain.get_dynamic_filter_options",
            callback: function (r) {
                if (r.message) {
                    const options = r.message; // Assuming it returns an array of strings
                    const filter = report.get_filter("po_created_user");
                    if (filter) {
                        // Update the options dynamically
                        filter.df.options = options.join("\n");
                        filter.refresh();
                    }
                }
            },
        });
    }
};
