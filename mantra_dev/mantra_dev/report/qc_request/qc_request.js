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

			frappe.db.get_value("Item", itemCode, "has_serial_no", function (r) {
				let isSerialized = r && r.has_serial_no ? r.has_serial_no : 0;

				frappe.prompt(
					[
						{
							label: "Quantity",
							fieldname: "qty",
							fieldtype: "Float",
							reqd: 1,
						},
						{
							label: "Serial Numbers",
							fieldname: "serial_no",
							fieldtype: "Long Text",
							reqd: isSerialized ? 1 : 0,
							description: isSerialized ? "Enter one serial number per line." : "",
						}
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
								message: __("Quantity cannot exceed QC Remaining QTY (" + qcRemainingQuantity + ")"),
							});
							return;

						}

						if (isSerialized) {
							let serialNumbers = values.serial_no.split("\n").map(sn => sn.trim()).filter(sn => sn);

							// Check if serial numbers are unique
							let uniqueSerialNumbers = new Set(serialNumbers);

							if (uniqueSerialNumbers.size !== serialNumbers.length) {
								frappe.msgprint({
									title: __("Validation Error"),
									indicator: "red",
									message: __("Duplicate serial numbers are not allowed."),
								});
								return;
							}

							if (serialNumbers.length !== values.qty) {
								frappe.msgprint({
									title: __("Validation Error"),
									indicator: "red",
									message: __("The number of serial numbers (" + serialNumbers.length + ") must match the quantity (" + values.qty + ")."),
								});
								return;
							}

							frappe.call({

								method: "mantra_dev.backend_code.qc_module.get_valid_serial_numbers",
								args: {
									purchase_receipt_id: purchaseReceiptId,
									item_code: itemCode,
									serial_numbers: values.serial_no ? values.serial_no.replace(/\n/g, ",") : ""  // Replace newlines with commas
								},

								callback: function (r) {

									if (r.message.status === "error") {
										frappe.msgprint({
											title: __("Validation Error"),
											indicator: "red",
											message: r.message.message,
										});
										return;
									}

									// If all serials are valid, proceed with the stock entry
									createStockEntry(purchaseReceiptId, purchaseReceiptItemId, itemCode, warehouse, values.qty, acceptedQuantity, qcProcessingQuantity, qcRemainingQuantity, values.serial_no);
								}
							});
						}
						else {
							// If not serialized, directly process the stock entry
							createStockEntry(purchaseReceiptId, purchaseReceiptItemId, itemCode, warehouse, values.qty, acceptedQuantity, qcProcessingQuantity, qcRemainingQuantity, values.serial_no);
						}
					},
					"Enter Quantity for QC Request",
					"Proceed"
				);
			});
		});

		function createStockEntry(purchaseReceiptId, purchaseReceiptItemId, itemCode, warehouse, qty, acceptedQuantity, qcProcessingQuantity, qcRemainingQuantity, serial_no) {
			frappe.call({
				method: "mantra_dev.backend_code.qc_module.create_draft_stock_entry_for_qc",
				args: {
					purchase_receipt: purchaseReceiptId,
					purchase_receipt_item_id: purchaseReceiptItemId,
					item_code: itemCode,
					warehouse: warehouse,
					qty: parseFloat(qty),
					serial_no: serial_no
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
				method: "mantra_dev.backend_code.qc_module.create_draft_stock_entry_for_material_transfer",
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
