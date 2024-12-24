// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["QC Request Approval"] = {
	"filters": [

	]
};

$(document).on("click", ".approve", function () {
	var button = $(this);


	var stockEntryId = button.data("stock_entry");


	// Approve drafted stock entry for material transfer
	frappe.call({
		method: "mantra_dev.backend_code.stock_entry.qc_request_stock_entry.appove_stock_entry",
		args: {
			stock_entry: stockEntryId,
		},
		callback: function (r) {
			if (r.message.status === "success") {
				frappe.msgprint(r.message.message);
				frappe.query_report.refresh();
			}
		},
		error: function () {
			frappe.msgprint(__("An error occurred while approving the Stock Entry."));
		}
	});
});
