// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["QC Stock Details"] = {
	"filters": [
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "MultiSelectList",
            "options": [],
            "reqd": 0,
            "get_data": function(txt) {
                return new Promise((resolve) => {
                    frappe.call({
                        method: "mantra_dev.mantra_dev.report.qc_stock_details.qc_stock_details.get_qc_warehouses",
                        callback: function(response) {
                            let options = response.message;
                            console.log(options);
                            resolve(options);
                        }
                    });
                });
            }
        }
    ],
};
