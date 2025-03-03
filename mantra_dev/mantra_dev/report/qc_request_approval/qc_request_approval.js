// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["QC Request Approval"] = {
	
	onload: function () {
		$(document).on("click", ".approvestockentry", function () {
			var button = $(this);
		
			var stockEntryId = button.data("stock_entry");
		
			// Approve drafted stock entry for material transfer
			frappe.call({
				method: "mantra_dev.backend_code.qc_module.approve_stock_entry",
				args: {
					stock_entry: stockEntryId,
				},
				callback: function (r) {
					if (r.message.status === "success") {
						frappe.msgprint(r.message.message);
						frappe.query_report.refresh();

						// After approving, send a notification
                        frappe.call({
                            method: "mantra_dev.backend_code.qc_module.send_notification",
                            args: {
                                doctype: "Stock Entry",
                                doc_name: stockEntryId,
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint(__("Notification Sent Successfully!"));
                                }
                            }
                        });
					}
				},
				error: function () {
					frappe.msgprint(__("An error occurred while approving the Stock Entry."));
				}
			});
		});
	},
};
