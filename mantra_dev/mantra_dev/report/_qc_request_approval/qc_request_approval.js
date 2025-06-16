// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["QC Request Approval"] = {

	onload: function () {
		$(document).on("click", ".approvestockentry", function () {
			var button = $(this);

			var stockEntryId = button.data("stock_entry");
			var itemCode = button.data("item_code");
			var qty = button.data("qty");
			var purchaseReceipt = button.data("purchase_receipt");


			frappe.db.get_value("Item", itemCode, "has_serial_no", function (r) {
				let isSerialized = r && r.has_serial_no ? r.has_serial_no : 0;

				if (isSerialized) {
					frappe.prompt(
						[
							{
								label: "Quantity",
								fieldname: "qty",
								fieldtype: "Float",
								default: qty,
								read_only: 1,
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

							if (serialNumbers.length !== parseInt(qty)) {
								frappe.msgprint({
									title: __("Validation Error"),
									indicator: "red",
									message: __("The number of serial numbers (" + serialNumbers.length + ") must match the quantity (" + parseInt(qty) + ")."),
								});
								return;
							}

							frappe.call({

								method: "mantra_dev.backend_code.qc_module.get_valid_serial_numbers",
								args: {
									purchase_receipt_id: purchaseReceipt,
									item_code: itemCode,
									serial_numbers: values.serial_no ? values.serial_no.replace(/\n/g, ",") : "" 
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

									// If serial numbers are valid, add them to stock entry and approve
                                    frappe.call({
                                        method: "mantra_dev.backend_code.qc_module.add_serial_numbers_and_approve",
                                        args: {
                                            stock_entry: stockEntryId,
                                            item_code: itemCode,
                                            serial_numbers: values.serial_no.replace(/\n/g, ",")  // Convert newlines to commas
                                        },
                                        callback: function (res) {
                                            if (res.message.status === "success") {
                                                frappe.msgprint(res.message.message);
                                                frappe.query_report.refresh();

                                            } else {
                                                frappe.msgprint({
                                                    title: __("Error"),
                                                    indicator: "red",
                                                    message: res.message.message,
                                                });
                                            }
                                        }
                                    });
                                }
                            });
                        },

						"Enter Serial No for QC",
						"Proceed"
					);
				} else {
					// Approve non-serialized stock entry directly
					frappe.call({
						method: "mantra_dev.backend_code.qc_module.approve_stock_entry",
						args: {
							stock_entry: stockEntryId,
						},
						callback: function (r) {
							if (r.message.status === "success") {
								frappe.msgprint(r.message.message);
								frappe.query_report.refresh();

							} else {
								frappe.msgprint({
									title: __("Error"),
									indicator: "red",
									message: res.message.message,
								});
							}
						},
						error: function () {
							frappe.msgprint(__("An error occurred while approving the Stock Entry."));
						}
					});
				}
			});
		});
	},
};
