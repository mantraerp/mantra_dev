// Copyright (c) 2024, Software At Work (India) Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Workflow TAT Report"] = {
	"filters": [
		{
			"fieldname": "doctype",
			"label": __("Doctype"),
			"fieldtype": "Link",
			"width": "80",
			"options": "DocType",
			"reqd": 1,
			get_query: function () {
				return {
					query: "mantra_dev.mantra_dev.report.workflow_tat_report.workflow_tat_report.get_dt_query",
				};
			},
		},
		{
			"fieldname": "docname",
			"label": __("DocName"),
			"fieldtype": "Dynamic Link",
			"width": "80",
			"options": "doctype",
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
		},
		{
			"fieldname": "delayed_by",
			"label": __("Delayed By"),
			"fieldtype": "Select",
			"options": "\n<1h\n<3h\n<6h\n<9h\n>1d\n>2d\n>1W\n>1M",
			"width": "80",
		}
	],
	 "formatter": function(value, row, column, data, default_formatter) {
		// if(row[1].content == undefined){
		// 	return "";
		// }
        if (column.fieldname === "time_variance") {  
            value = default_formatter(value, row, column, data);
            
            if (typeof value === "string" && value.startsWith("-")) {
                value = `<span style="color:red;">${value}</span>`;
            } else {
                value = `<span style="color:green;">${value}</span>`;
            }
        } else {
            value = default_formatter(value, row, column, data);
        }
        
        return value;
    }
};
