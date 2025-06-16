// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["QC Request"] = {

	onload: function () {
		$(document).on("click", ".qcrequest", function () {
			var button = $(this);


			var purchaseReceiptId = button.data("id");
			var purchaseReceiptItemId = button.data("purchase-receipt-item-id");
			var itemCode = button.data("item_code");
			var warehouse = button.data("warehouse");
			var acceptedQuantity = button.data("accepted_quantity");
			var qcProcessingQuantity = button.data("qc_processing_quantity");
			var qcRemainingQuantity = button.data("qc_remaining_quantity");

			frappe.prompt(
				[
					{
						label: "Quantity",
						fieldname: "qty",
						fieldtype: "Float",
						reqd: 1,
					},
				],
				(values) => {

					if (values.qty <= 0) {
						frappe.msgprint({
							title: __("Validation Error"),
							indicator: "red",
							message: __("Quantity should be greater than 0."),
						});
						return;

					}

					// Validation: Ensure entered qty does not exceed QC Remaining QTY
					if (values.qty > qcRemainingQuantity) {
						frappe.msgprint({
							title: __("Validation Error"),
							indicator: "red",
							message: __("Quantity cannot exceed QC Remaining QTY (" + parseFloat(qcRemainingQuantity) + ")"),
						});
						return;

					}

					createStockEntry(purchaseReceiptId, purchaseReceiptItemId, itemCode, warehouse, values.qty, acceptedQuantity, qcProcessingQuantity, qcRemainingQuantity);
				},
				"Enter Quantity for QC Request",
				"Proceed"
			);
		});

		function createStockEntry(purchaseReceiptId, purchaseReceiptItemId, itemCode, warehouse, qty, acceptedQuantity, qcProcessingQuantity, qcRemainingQuantity) {
			frappe.call({
				method: "mantra_dev.backend_code.qc_module.create_draft_stock_entry_for_qc",
				args: {
					purchase_receipt: purchaseReceiptId,
					purchase_receipt_item_id: purchaseReceiptItemId,
					item_code: itemCode,
					warehouse: warehouse,
					qty: parseFloat(qty),
				},
				callback: function (r) {
					if (!r.exc) {
						frappe.msgprint(__("Stock Entry created: {0}", [r.message]));

						let newQcProcessingQty = parseFloat(parseFloat(qcProcessingQuantity) + parseFloat(qty));
						let newQcRemainingQty = parseFloat(parseFloat(qcRemainingQuantity) - parseFloat(qty));

						if (parseFloat((parseFloat(newQcProcessingQty) + parseFloat(newQcRemainingQty))) !== parseFloat(acceptedQuantity)) {
							frappe.msgprint({
								title: __("Validation Error"),
								indicator: "red",
								message: __("QC Processing (" + newQcProcessingQty + ") + QC Remaining (" + newQcRemainingQty + ") must equal Accepted Quantity (" + acceptedQuantity + ")."),
							});
							return;
						}

						frappe.call({
							method: "mantra_dev.backend_code.qc_module.update_qc_quantities",
							args: {
								purchase_receipt_item_id: purchaseReceiptItemId,
								new_qc_processing_qty: parseFloat(newQcProcessingQty),
								new_qc_remaining_qty: parseFloat(newQcRemainingQty)
							},
							callback: function (response) {
								console.log(response); // Debugging
								if (response.message && response.message.status === "success") {
									frappe.msgprint(response.message.message);
									frappe.query_report.refresh();
								} else {
									frappe.msgprint(__("Failed to update QC quantities. Check logs."));
								}
							}
						});

					} else {
						frappe.throw(__("Stock Entry creation failed."));
						return;
					}
				}
			});
		}

		$(document).on("click", ".stocktransfer", function () {
			var button = $(this);

			var purchaseReceiptId = button.data("id");
			var purchaseReceiptItemId = button.data("purchase-receipt-item-id");
			var itemCode = button.data("item_code");
			var warehouse = button.data("warehouse");
			var acceptedQuantity = button.data("accepted_quantity");
			var qcProcessingQuantity = button.data("qc_processing_quantity");
			var qcRemainingQuantity = button.data("qc_remaining_quantity");

			// If inspection not required for particular item then make drafted stock entry from Default Inward Warehouse to Default QC Accepted Warehouse
			frappe.call({
				method: "mantra_dev.backend_code.qc_module.create_stock_entry_for_material_transfer",
				args: {
					purchase_receipt: purchaseReceiptId,
					item_code: itemCode,
					warehouse: warehouse,
					purchase_receipt_item_id: purchaseReceiptItemId,
					// qty: parseFloat(values.qty)
				},
				callback: function (r) {
					if (!r.exc) {

						frappe.msgprint(__("Stock Entry created: {0}", [r.message]));
						frappe.query_report.refresh();
					}
					else {
						frappe.throw(__("Stock Entry creation failed."));
						return
					}
				}
			});

		});

	},
};
