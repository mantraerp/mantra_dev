// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["QC Request"] = {
	"filters": [

	]
};

$(document).on("click", ".qcrequest", function () {
	var button = $(this);


	var purchaseReceiptId = button.data("id");
	var itemCode = button.data("item-code");
	var warehouse = button.data("warehouse");


	// If inspection required for particular item then make drafted stock entry from Default Inward Warehouse to Default QC Processing Warehouse
	frappe.call({
		method: "mantra_dev.backend_code.stock_entry.qc_request_stock_entry.create_draft_stock_entry_for_qc",
		args: {
			purchase_receipt: purchaseReceiptId,
			item_code: itemCode,
			warehouse: warehouse,
		},
		callback: function (r) {
			if (!r.exc) {
				frappe.msgprint(__("Stock Entry created: {0}", [r.message]));
				frappe.query_report.refresh();
			}
		}
	});
});




$(document).on("click", ".stocktransfer", function () {
	var button = $(this);


	var purchaseReceiptId = button.data("id");
	var itemCode = button.data("item-code");
	var warehouse = button.data("warehouse");


	// If inspection not required for particular item then make drafted stock entry from Default Inward Warehouse to Default QC Accepted Warehouse
	frappe.call({
		method: "mantra_dev.backend_code.stock_entry.qc_request_stock_entry.create_draft_stock_entry_for_material_transfer",
		args: {
			purchase_receipt: purchaseReceiptId,
			item_code: itemCode,
			warehouse: warehouse,
		},
		callback: function (r) {
			if (!r.exc) {
				frappe.msgprint(__("Stock Entry created: {0}", [r.message]));
				frappe.query_report.refresh();
			}
		}
	});
});
