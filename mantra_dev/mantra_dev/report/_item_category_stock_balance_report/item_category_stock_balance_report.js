// Define a new script report
frappe.query_reports["Item Category Stock Balance Report"] = {
    "filters": [
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "default": ""
        }
    ],

    // Customize the result
    onload: function(report) {
        report.page.set_title(__("Item Category Stock Balance Report"));
    },

    // Additional customizations for the report can be done here
    // For example, adding buttons, event listeners, etc.
};
