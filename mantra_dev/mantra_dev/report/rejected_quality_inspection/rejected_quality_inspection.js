// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Rejected Quality Inspection"] = {
	onload: function () {
		$(document).on("click", ".stockentryforrework, .stockentryforreturn", function () {
			var button = $(this);
			var qualityInspectionId = button.data("quality_inspection");
			var rejectedStockEntry = button.data("stock_entry");
			var method = button.hasClass('stockentryforrework') ? "mantra_dev.backend_code.qc_module.stock_entry_for_rework" : "mantra_dev.backend_code.qc_module.stock_entry_for_return";

			// Create stock entry for rework or return
			frappe.call({
				method: method,
				args: {
					quality_inspection: qualityInspectionId,
					rejected_stock_entry: rejectedStockEntry,
					workflow_save: true,
				},
				callback: function (r) {
					if (r.message.status === "success") {
						frappe.msgprint(r.message.message);
						frappe.query_report.refresh();
					}
				},
				error: function () {
					frappe.msgprint(__("An error occurred while creating the Stock Entry."));
				}
			});
		});
	},
};