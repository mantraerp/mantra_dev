// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Quality Inspection Approval"] = {
	"filters": [

	]
};

$(document).on("click", ".approve", function () {
	var button = $(this);


	var qualityInspectionId = button.data("quality_inspection");
	var status = button.data("status");


	// Approve or Reject Quality inspection and create stock entry for material transfer
	frappe.call({
		method: "mantra_dev.backend_code.stock_entry.qc_request_stock_entry.quality_inspection_approval",
		args: {
			quality_inspection: qualityInspectionId,
			status: status,
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
