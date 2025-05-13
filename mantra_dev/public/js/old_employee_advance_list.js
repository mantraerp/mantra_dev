// frappe.listview_settings['Employee Advance'] = {
//     onload: function (listview) {
//         listview.page.add_action_item(__("Payment"), () => {
//             erpnext.bulk_transaction_processing.create(listview, "Employee Advance", "Payment Entry");
//         });
//     }
// };






// frappe.listview_settings['Employee Advance'] = {
//     onload: function (listview) {
//         listview.page.add_action_item(__("Payment"), () => {
//             erpnext.bulk_transaction_processing.create(
//                 listview,
//                 "Employee Advance",
//                 "Payment Entry"
//             );
//         });

//         // Register the mapping method
//         if (!erpnext.bulk_transaction_processing.payment_mappings) {
//             erpnext.bulk_transaction_processing.payment_mappings = {};
//         }

//         erpnext.bulk_transaction_processing.payment_mappings["Employee Advance"] =
//             "mantra_dev.backend_code.api.make_payment_entry";
//     }
// };


frappe.listview_settings['Employee Advance'] = {
    onload: function (listview) {
        listview.page.add_action_item(__("Payment"), () => {
            const selected_docs = listview.get_checked_items(true);
            if (!selected_docs.length) {
                frappe.msgprint(__("Please select at least one Employee Advance."));
                return;
            }

            frappe.call({
                method: "mantra_dev.backend_code.api.make_payment_entries",
                args: {
                    source_names: selected_docs
                },
                callback: function (response) {
                    frappe.msgprint(__("Payment processing complete."));
                    listview.refresh();
                }
            });
        });
    }
};