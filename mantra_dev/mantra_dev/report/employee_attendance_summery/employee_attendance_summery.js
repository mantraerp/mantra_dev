// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Attendance Summery"] = {
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
				for (let i = 2023; i <= current_year; i++) {
					years.push({ "value": i.toString(), "label": i.toString() });
				}
				return years;
			})(),
			"default": new Date().getFullYear().toString()
		},
	],
	after_datatable_render: function (table_instance) {
        table_instance.datamanager.data.forEach((row, rowIdx) => {
			console.log(row['present_days'] + row['absent_days'] + row['taken_leave'] + row['no_of_holiday'] + row['no_of_weekoff'])
			console.log("total", row['total_days'])
            if (row['present_days'] + row['absent_days'] + row['taken_leave'] + row['no_of_holiday'] + row['no_of_weekoff'] != row['total_days'] - row['days_difference']) {
                color_single_row(table_instance, rowIdx,'#ff000040 !important');
            } else {
				color_single_row(table_instance, rowIdx, 'transparent !important'); // Reset to default
			}
        });
    },
	"onload": function(report){
		$("textarea[data-fieldname='employee_list']").css({'height':'60'});
	}
};

function color_single_row(table_instance, rowIdx,color) {
    for (let col = 0; col < Object.entries(table_instance.datamanager.columns).length; col++) {
        table_instance.style.setStyle(`.dt-cell--${col}-${rowIdx}`, { backgroundColor: `${color}` });
    }
}