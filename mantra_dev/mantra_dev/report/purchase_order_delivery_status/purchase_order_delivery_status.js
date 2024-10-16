frappe.query_reports["Purchase Order Delivery Status"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "Pending Qty" && data && data["Pending Qty"] > 0) {
            value = `<span style="color:orange;">${value}</span>`;
        }
        return value;
    },
    "onload": function (report) {
        report.page.add_inner_button(__("Refresh"), function () {
            report.refresh();
        });
    }
};
