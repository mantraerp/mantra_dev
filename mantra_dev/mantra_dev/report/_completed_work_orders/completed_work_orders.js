// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Completed Work Orders"] = {
    "filters": [],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        // Example custom formatting (if needed)
        if (column.fieldname === "Work Order") {
            value = `<a href="#Form/Work Order/${data["Work Order"]}">${value}</a>`;
        }
        return value;
    }
};
