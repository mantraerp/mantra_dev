// Path: [your_module]/report/SalesInvoiceByCostCenter/SalesInvoiceByCostCenter.js

frappe.query_reports["Sales by Cost Center and Salesperson"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "sales_person",
            label: __("Sales Person"),
            fieldtype: "Link",
            options: "Sales Person",
            get_query: function() {
                return {
                    filters: {
                        enabled: 1
                    }
                }
            }
        }
    ],

    onload: function(report) {
        report.page.add_inner_button(__("Refresh"), function() {
            report.refresh();
        });
    }
};
