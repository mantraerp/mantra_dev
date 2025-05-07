// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Document Workflow TAT Report"] = {
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
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
        if (!["doctype", "document_name", "draft", "default_time", "diff"].includes(column.fieldname)) {
            value = default_formatter(value, row, column, data);
            
            if (typeof value === "string" && value.startsWith("-")) {
                value = `<span style="color:red;">${value}</span>`;
            } else if (value != '0s') {
                value = `<span style="color:green;">${value}</span>`;
            }
        } else {
            value = default_formatter(value, row, column, data);
        }
        
        return value;
    },
	onload: function (report) {
		const style = `
			<style>
				.report-summary .summary-value.purple {
					color: #17a2b8 !important;
				}
			</style>
		`;
		$('head').append(style);
	}	
};
