// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Quality Inspection Approval"] = {
	
	onload: function () {
		// $(document).on("click", ".qualityinspectionapprove", function () {
		// 	var button = $(this);


		// 	var qualityInspectionId = button.data("quality_inspection");
		// 	var actualQty = button.data("actual_qty");
		// 	var status = button.data("status");


		// 	// Approve or Reject Quality inspection and create stock entry for material transfer
		// 	frappe.call({
		// 		method: "mantra_dev.backend_code.qc_module.quality_inspection_approval",
		// 		args: {
		// 			quality_inspection: qualityInspectionId,
		// 			actual_qty: actualQty,
		// 			status: status,
		// 		    workflow_save: true,
		// 		},
		// 		callback: function (r) {
		// 			if (r.message.status === "success") {
		// 				frappe.msgprint(r.message.message);
		// 				frappe.query_report.refresh();
		// 			}
		// 		},
		// 		error: function () {
		// 			frappe.msgprint(__("An error occurred while approving the Stock Entry."));
		// 		}
		// 	});
		// });
	},
};
