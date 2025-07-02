frappe.query_reports["Sales Flow with nos"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -7),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ],

    "onload": function(report) {
        // Custom code that runs when the report is loaded
    },

    "formatter": function(value, row, column, data, default_formatter) {
        // Custom formatting for report cells
        value = default_formatter(value, row, column, data);
        
        // Example: Highlight rows based on a condition
        if (column.fieldname == "sales_order" && data && data.sales_order) {
            value = `<span style="color:blue">${value}</span>`;
        }

        return value;
    },

    "get_datatable_options": function(options) {
        // Custom options for the DataTable
        return Object.assign(options, {
            // Example: freeze the first column
            freezeFirstColumn: true
        });
    }
};
