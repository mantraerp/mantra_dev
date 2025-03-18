frappe.ui.form.on("Quality Inspection", {
    setup: function (frm) {
        frm.set_query("item_code", function () {
            // Filter Items based on warehouse mentioned in QC Settings --> Default QC Processing Warehouse
            return {
                query: "mantra_dev.backend_code.qc_module.get_items_from_warehouse",
            };
        });

        frm.set_query("item_serial_no", function () {
            if (!frm.doc.item_code) {
                frappe.msgprint(__("Please select an Item Code first."));
                return;
            }

            // Filter Item Serial No based on selected Item Code and warehouse mentioned in QC Settings --> Default QC Processing Warehouse
            return {
                query: "mantra_dev.backend_code.qc_module.get_serial_nos",
                filters: {
                    item_code: frm.doc.item_code,
                },
            };
        });

        frm.set_query("quality_inspection_template", function () {
            if (!frm.doc.item_code) {
                frappe.msgprint(__("Please select an Item Code first."));
                return;
            }

            // Fetch Quality Inspection Template from Item master Quality Inspection Template field
            return {
                query: "mantra_dev.backend_code.qc_module.get_quality_inspection_templates",
                filters: {
                    item_code: frm.doc.item_code,
                },
            };
        });

        frm.fields_dict.batch_no.get_query = function (doc) {
            if (!doc.item_code) {
                frappe.msgprint(__("Please select an Item Code first."));
                return;
            }

            // Filter Batch No based on selected Item Code and warehouse mentioned in QC Settings --> Default QC Processing Warehouse
            return {
                query: "mantra_dev.backend_code.qc_module.get_batch_nos",
                filters: {
                    item_code: doc.item_code,
                },
            };
        };
    },

    item_code: function (frm) {
        frm.set_value("item_serial_no", "")
        // frm.set_value("batch_no", "")
        frm.set_value("sample_size", 0)
        // frm.set_value("custom_actual_qty", 0)

        // Fetch and Set Quality Inspection Template from Item master Quality Inspection Template field and accordingly set Readings child table on Item Code change
        if (frm.doc.item_code) {
            frm.set_value("item_serial_no", "")
            // frm.set_value("batch_no", "")
            frm.set_value("sample_size", 0)
            // frm.set_value("custom_actual_qty", 0)

            frappe.call({
                method: "mantra_dev.backend_code.qc_module.get_item_details",
                args: { item_code: frm.doc.item_code },
                callback: function (r) {
                    if (r.message && !r.message.error) {

                        frm.set_value("quality_inspection_template", r.message.quality_inspection_template || "");

                        if (!r.message.quality_inspection_template) {
                            frm.clear_table("readings");
                            frm.refresh_field("readings");
                        }

                        let hasBatch = r.message.has_batch_no;
                        let hasSerial = r.message.has_serial_no;

                        frm.set_df_property("batch_no", "reqd", hasBatch ? 1 : 0);
                        frm.set_df_property("item_serial_no", "reqd", hasSerial ? 1 : 0);

                    } else {
                        frm.set_value("quality_inspection_template", "");
                        frm.clear_table("readings");
                        frm.refresh_field("readings");

                        frm.set_df_property("batch_no", "reqd", 0);
                        frm.set_df_property("item_serial_no", "reqd", 0);
                    }
                }
            });
        } else {
            frm.set_value("quality_inspection_template", "");
            frm.clear_table("readings");
            frm.refresh_field("readings");

            frm.set_df_property("batch_no", "reqd", 0);
            frm.set_df_property("item_serial_no", "reqd", 0);
        }

    },

    item_serial_no: function (frm) {

        if (frm.doc.item_serial_no) {
            // If item has serial no and batch no both and if serial no is selected then set the batch no of that serial no
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.get_serial_batch",
                args: { serial_no: frm.doc.item_serial_no },
                callback: function (r) {
                    if (r.message && r.message.batch_no) {
                        frm.set_value("batch_no", r.message.batch_no);

                        frm.set_query("batch_no", function () {
                            return {
                                filters: {
                                    name: r.message.batch_no
                                }
                            };
                        });

                    } else {
                        frm.set_value("batch_no", "");
                    }
                }
            });
        } else {
            // frm.set_value("batch_no", "");
            frm.fields_dict.batch_no.get_query = function (doc) {
                // Filter Batch No based on selected Item Code and warehouse mentioned in QC Settings --> Default QC Processing Warehouse
                return {
                    query: "mantra_dev.backend_code.qc_module.get_batch_nos",
                    filters: {
                        item_code: doc.item_code,
                    },
                };
            };
        }
    },


    batch_no: function (frm) {

        if (frm.doc.batch_no) {
            // if item has serial no and batch no both and if batch no is selected then filter serial no of that batch
            frm.set_query("item_serial_no", function () {
                return {
                    filters: {
                        batch_no: frm.doc.batch_no
                    }
                };
            });
        } else {
            frm.set_query("item_serial_no", function () {
                // Filter Item Serial No based on selected Item Code and warehouse mentioned in QC Settings --> Default QC Processing Warehouse
                return {
                    query: "mantra_dev.backend_code.qc_module.get_serial_nos",
                    filters: {
                        item_code: frm.doc.item_code,
                    },
                };
            });
        }
    },


    sample_size: function (frm) {
        if (!frm.doc.item_code) {
            frappe.msgprint(__("Please select an Item Code first."));
            return;
        }

        if (frm.doc.custom_actual_qty && frm.doc.sample_size > frm.doc.custom_actual_qty) {
            frappe.msgprint(__("Sample Size cannot be greater than the Actual QTY ({0}).".replace("{0}", frm.doc.custom_actual_qty)));
            frm.set_value("sample_size", frm.doc.custom_actual_qty);
            return;
        }

        if (frm.doc.item_serial_no) {
            // If item has a serial number, sample size should be exactly 1
            if (frm.doc.sample_size !== 1) {
                frappe.msgprint(__("Sample Size must be exactly 1 for a serialized Item."));
                frm.set_value("sample_size", 1);
            }
        }

        else if (frm.doc.batch_no) {
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.get_qc_processing_warehouse",
                callback: function (res) {
                    if (res.message && res.message.qc_processing_warehouse) {
                        const qc_processing_warehouse = res.message.qc_processing_warehouse;

                        // if item has batch no then sample size can not exceed batch qty available in QC Processing Warehouse
                        frappe.call({
                            method: "erpnext.stock.doctype.batch.batch.get_batch_qty",
                            args: {
                                batch_no: frm.doc.batch_no,
                                warehouse: qc_processing_warehouse
                            },
                            callback: function (r) {
                                if (r.message) {
                                    const available_qty = r.message;
                                    // console.log(available_qty);
                                    if (frm.doc.sample_size > available_qty) {
                                        frappe.msgprint(__("Sample Size cannot exceed the available batch quantity ({0}) in the warehouse.".replace("{0}", available_qty)));
                                        frm.set_value("sample_size", available_qty);
                                    }
                                }
                            }
                        });
                    } else {
                        frappe.msgprint(__("QC Processing Warehouse is not configured in QC Settings."));
                    }
                }
            });
        }

        else {

            // Sample Size can not exceed total No of Items in QC Settings --> Default QC Processing Warehouse
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.get_available_qty",
                args: {
                    item_code: frm.doc.item_code,
                },
                callback: function (r) {
                    if (!r.exc && r.message !== undefined) {
                        const available_qty = r.message;
                        if (frm.doc.sample_size > available_qty) {
                            frappe.msgprint(__("Sample Size cannot exceed the available quantity ({0}) in the warehouse.".replace("{0}", available_qty)));
                            frm.set_value("sample_size", available_qty);
                        }
                    }
                }
            });
        }
    },

    custom_actual_qty: function (frm) {
        if (!frm.doc.item_code) {
            frappe.msgprint(__("Please select an Item Code first."));
            return;
        }

        if (frm.doc.sample_size && frm.doc.custom_actual_qty < frm.doc.sample_size) {
            frappe.msgprint(__("Actual QTY cannot be less than the Sample Size ({0}).".replace("{0}", frm.doc.sample_size)));
            frm.set_value("custom_actual_qty", frm.doc.sample_size);
            return;
        }

        if (frm.doc.reference_type == "Stock Entry" && frm.doc.reference_name) {
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.get_stock_entry_details",
                args: {
                    reference_name: frm.doc.reference_name
                },
                callback: function (r) {
                    if (r.message) {
                        const custom_actual_qty = r.message.custom_actual_qty;
                        if (frm.doc.custom_actual_qty > custom_actual_qty) {
                            frappe.msgprint(__("Actual QTY cannot exceed the available quantity ({0}) in the Stock Entry.".replace("{0}", custom_actual_qty)));
                            frm.set_value("custom_actual_qty", custom_actual_qty);
                        }
                    }
                }
            });
        }

        if (frm.doc.item_serial_no) {
            // if item has serial no then actual qty should be exactly 1
            if (frm.doc.custom_actual_qty !== 1) {
                frappe.msgprint(__("Actual QTY must be exactly 1 for a serialized Item."));
                frm.set_value("custom_actual_qty", 1);
            }
        }

        else if (frm.doc.batch_no) {
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.get_qc_processing_warehouse",
                callback: function (res) {
                    if (res.message && res.message.qc_processing_warehouse) {
                        const qc_processing_warehouse = res.message.qc_processing_warehouse;

                        // if item has batch no then actual qty can not exceed batch qty available in QC Processing Warehouse
                        frappe.call({
                            method: "erpnext.stock.doctype.batch.batch.get_batch_qty",
                            args: {
                                batch_no: frm.doc.batch_no,
                                warehouse: qc_processing_warehouse
                            },
                            callback: function (r) {
                                if (r.message) {
                                    const available_qty = r.message;
                                    if (frm.doc.custom_actual_qty > available_qty) {
                                        frappe.msgprint(__("Actual QTY cannot exceed the available batch quantity ({0}) in the warehouse.".replace("{0}", available_qty)));
                                        frm.set_value("custom_actual_qty", available_qty);
                                    }
                                }
                            }
                        });
                    } else {
                        frappe.msgprint(__("QC Processing Warehouse is not configured in QC Settings."));
                    }
                }
            });
        }

        else {

            // Actual Qty can not exceed total No of Items in QC Settings --> Default QC Processing Warehouse
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.get_available_qty",
                args: {
                    item_code: frm.doc.item_code,
                },
                callback: function (r) {
                    if (!r.exc && r.message !== undefined) {
                        const available_qty = r.message;
                        if (frm.doc.custom_actual_qty > available_qty) {
                            frappe.msgprint(__("Actual QTY cannot exceed the available quantity ({0}) in the warehouse.".replace("{0}", available_qty)));
                            frm.set_value("custom_actual_qty", available_qty);
                        }
                    }
                }
            });
        }

    },

    reference_name: function (frm) {
        if (frm.doc.reference_type == "Stock Entry" && frm.doc.reference_name) {
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.get_stock_entry_details",
                args: {
                    reference_name: frm.doc.reference_name
                },
                callback: function (r) {
                    if (r.message) {
                        const custom_actual_qty = r.message.custom_actual_qty;
                        if (frm.doc.custom_actual_qty > custom_actual_qty) {
                            frappe.msgprint(__("Actual QTY cannot exceed the available quantity ({0}) in the Stock Entry.".replace("{0}", custom_actual_qty)));
                            frm.set_value("custom_actual_qty", custom_actual_qty);
                        }
                    }
                }
            });

        }
    },

    before_save: function (frm) {
        if (frm.doc.sample_size <= 0) {
            frappe.throw("Sample size should be greater than 0.")
        }
        if (frm.doc.custom_actual_qty <= 0) {
            frappe.throw("Actual QTY should be greater than 0.")
        }
    },

    refresh: function (frm) {
        // if workflow state Approved, Rework or Return then add custom button 'Generate QR Code' for QR code
        if (["Approved", "Rework", "Return"].includes(frm.doc.workflow_state)) {
            frm.add_custom_button("Generate QR Code", function () {

                let report_date = frm.doc.report_date;
                let item_code = frm.doc.item_code;
                let item_name = frm.doc.item_name;
                let serial_no = frm.doc.item_serial_no || "";
                let batch_no = frm.doc.batch_no || "";
                let sample_size = frm.doc.sample_size;
                let actual_qty = frm.doc.custom_actual_qty;

                if (report_date) {
                    report_date = frappe.datetime.str_to_user(report_date); // Converts to user's date format
                }

                // let qr_url = `http://192.168.5.78:8000/quality_inspection_details?name=${frm.doc.name}`;
                // let qr_url = `${window.location.origin}/quality_inspection_details?name=${frm.doc.name}`;
                let qr_url = `${window.location.origin}/quality_inspection_details?name=${frm.doc.name}&item_code=${item_code}&item_name=${item_name}&report_date=${report_date}&serial_no=${serial_no}&batch_no=${batch_no}&sample_size=${sample_size}&actual_qty=${actual_qty}`;

                let qr_code_url = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qr_url)}&size=200x200`;

                // let qr_url = `http://192.168.5.78:8000/quality_inspection_details?name=${frm.doc.name}&item_code=${item_code}&item_name=${item_name}&report_date=${report_date}&serial_no=${serial_no}&batch_no=${batch_no}&sample_size=${sample_size}&actual_qty=${actual_qty}`;

                // // Use the API to generate the QR code image with this URL
                // let qr_code_url = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qr_url)}&size=200x200`;


                // Wait for the field to update, then print only the QR code
                setTimeout(function () {
                    let printWindow = window.open("", "_blank");
                    printWindow.document.write(`
                        <html>
                        <head>
                            <style>
                                body { margin: 0; padding: 0; }
                                .qr-container {
                                    position: absolute;
                                    top: 10px;
                                    left: 10px;
                                }
                                img { width: 100px; height: 100px; }
                            </style>
                        </head>
                        <body>
                            <div class="qr-container">
                                <img src="${qr_code_url}" alt="QR Code">
                            </div>
                            <script>
                                window.onload = function () {
                                    window.print();
                                    setTimeout(() => window.close(), 500);
                                };
                            </script>
                        </body>
                        </html>
                    `);
                    printWindow.document.close();
                }, 500);

                // let report_date = frm.doc.report_date;
                // let item_code = frm.doc.item_code;
                // let item_name = frm.doc.item_name;
                // let serial_no = frm.doc.item_serial_no || "";
                // let batch_no = frm.doc.batch_no || "";
                // let sample_size = frm.doc.sample_size;
                // let actual_qty = frm.doc.custom_actual_qty;

                // if (report_date) {
                //     report_date = frappe.datetime.str_to_user(report_date); // Converts to user's date format
                // }

                // let qr_url = `http://192.168.5.78:8000/quality_inspection_details?name=${frm.doc.name}&item_code=${item_code}&item_name=${item_name}&report_date=${report_date}&serial_no=${serial_no}&batch_no=${batch_no}&sample_size=${sample_size}&actual_qty=${actual_qty}`;

                // // Use the API to generate the QR code image with this URL
                // let qr_code_url = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qr_url)}&size=200x200`;

                // // Open the QR code in a new tab
                // window.open(qr_code_url, "_blank");
            });
        }
    },

    before_workflow_action(frm) {
        // If Quality Inspection status is Rejected, can not Approve that document
        if (frm.doc.workflow_state === "Approval Requested" && frm.selected_workflow_action === 'Approve' && frm.doc.status === "Rejected") {
            frappe.dom.unfreeze();
            frappe.throw(__("Rejected Quality Inspection cannot be approved."));

        }

        // If Quality Inspection status is Accepted, can not Reject that document
        else if (frm.doc.workflow_state === "Approval Requested" && frm.selected_workflow_action === 'Reject' && frm.doc.status === "Accepted") {
            frappe.dom.unfreeze();
            frappe.throw(__("Approved Quality Inspection cannot be rejected."));
        }

        // If Quality Inspection status is Accepted and Approve that document or Quality Inspection status is Rejected and Reject that document
        else if (
            frm.doc.workflow_state === "Approval Requested" &&
            (frm.selected_workflow_action === "Approve" || frm.selected_workflow_action === "Reject")
        ) {

            return new Promise((resolve, reject) => {
                frappe.call({
                    method: "mantra_dev.backend_code.qc_module.quality_inspection_approval",
                    args: {
                        quality_inspection: frm.doc.name,
                        actual_qty: frm.doc.custom_actual_qty,
                        status: frm.doc.status,
                        workflow_save: false,
                    },
                    callback: function (r) {
                        if (r.message.status === "success") {
                            frappe.msgprint(r.message.message);
                            resolve(); // Continue with the workflow
                        } else {
                            frappe.dom.unfreeze();
                            frappe.throw(__("An error occurred while creating the Stock Entry."));
                            reject(); // Stop the workflow
                        }
                    },
                    error: function () {
                        frappe.dom.unfreeze();
                        frappe.throw(__("An error occurred while creating the Stock Entry."));
                        reject(); // Stop the workflow

                    },
                });
            });
        }

        // If Quality Inspection status is Rejected and Process that document for Rework
        else if (
            frm.doc.workflow_state === "Rejected" && frm.selected_workflow_action === "Process"
        ) {

            return new Promise((resolve, reject) => {
                frappe.call({
                    method: "mantra_dev.backend_code.qc_module.stock_entry_for_rework",
                    args: {
                        quality_inspection: frm.doc.name,
                        rejected_stock_entry: frm.doc.custom_stock_entry,
                        workflow_save: false,
                    },
                    callback: function (r) {
                        if (r.message.status === "success") {
                            frappe.msgprint(r.message.message);
                            resolve(); // Continue with the workflow
                        } else {
                            frappe.dom.unfreeze();
                            frappe.throw(__("An error occurred while creating the Stock Entry."));
                            reject(); // Stop the workflow
                        }
                    },
                    error: function () {
                        frappe.dom.unfreeze();
                        frappe.throw(__("An error occurred while creating the Stock Entry."));
                        reject(); // Stop the workflow

                    },
                });
            });
        }

        // If Quality Inspection status is Rejected and Return that document for Return
        else if (
            frm.doc.workflow_state === "Rejected" && frm.selected_workflow_action === "Return"
        ) {

            return new Promise((resolve, reject) => {
                frappe.call({
                    method: "mantra_dev.backend_code.qc_module.stock_entry_for_return",
                    args: {
                        quality_inspection: frm.doc.name,
                        rejected_stock_entry: frm.doc.custom_stock_entry,
                        workflow_save: false,
                    },
                    callback: function (r) {
                        if (r.message.status === "success") {
                            frappe.msgprint(r.message.message);
                            resolve(); // Continue with the workflow
                        } else {
                            frappe.dom.unfreeze();
                            frappe.throw(__("An error occurred while creating the Stock Entry."));
                            reject(); // Stop the workflow
                        }
                    },
                    error: function () {
                        frappe.dom.unfreeze();
                        frappe.throw(__("An error occurred while creating the Stock Entry."));
                        reject(); // Stop the workflow

                    },
                });
            });
        }

    },

    after_workflow_action(frm) {
        if (frm.doc.workflow_state == "Approval Requested") {
            // Send notification to particular user (Quality Manager)
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.send_notification",
                args: {
                    doctype: "Quality Inspection",
                    doc_name: frm.doc.name,
                },
                callback: function (r) {
                    if (!r.exc) {
                        frappe.msgprint(__("Notification Sent Successfully!"));
                    }
                }
            });
        }

        if (frm.doc.workflow_state === "Approved" || frm.doc.workflow_state === "Rejected") {
            frappe.call({
                method: "mantra_dev.backend_code.qc_module.update_qc_done_qty",
                args: { qi_name: frm.doc.name },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__(r.message));
                    }
                }
            });
        }
    }
});