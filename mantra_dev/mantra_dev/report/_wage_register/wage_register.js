// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Wage Register"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "MultiSelectList",
			"options": "Employee",
			"get_data": function(txt) {
				return frappe.db.get_link_options("Employee", txt);
			}
		},
		{
			"fieldname": "employee_list",
			"label": __("Employee List"),
			"fieldtype": "Small Text"
		},
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": [
				{ "value": "01", "label": "January" },
				{ "value": "02", "label": "February" },
				{ "value": "03", "label": "March" },
				{ "value": "04", "label": "April" },
				{ "value": "05", "label": "May" },
				{ "value": "06", "label": "June" },
				{ "value": "07", "label": "July" },
				{ "value": "08", "label": "August" },
				{ "value": "09", "label": "September" },
				{ "value": "10", "label": "October" },
				{ "value": "11", "label": "November" },
				{ "value": "12", "label": "December" }
			],
			"default": (new Date().getMonth() + 1).toString().padStart(2, '0')  // Set current month as default
		},
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Select",
			"options": (function() {
				let current_year = new Date().getFullYear();
				let years = [];
				for (let i = current_year - 4; i <= current_year; i++) {
					years.push({ "value": i.toString(), "label": i.toString() });
				}
				return years;
			})(),
			"default": new Date().getFullYear().toString()
		},
		{
			"fieldname": "based_on_location",
			"label": __("Payment Location Based On"),
			"fieldtype": "Select",
			"options": "Company HO\nEmlpoyee Branch",
			"default": "Company HO"
		}
	],
	"onload": function(report){
		$("textarea[data-fieldname='employee_list']").css({'height':'60'});
		report.page.add_inner_button(__("Download Wage Register"), function() {
            frappe.call({
				method: "mantra_dev.mantra_dev.report.wage_register.wage_register.download_excel",
				args: {
					report_data: report.data,
					month: frappe.query_report.get_filter_value('month'),
					year: frappe.query_report.get_filter_value('year')
				},
				callback: function(r) {
					if (r.message) {
						var link_element = document.createElement('a');
						link_element.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,' + r.message.file_content;
						link_element.download = r.message.file_name;
						link_element.click();
					} else {
						frappe.msgprint(__('No data found for the selected filters.'));
					}
				}
			});
        });
	}
};
