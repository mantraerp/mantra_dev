frappe.ui.form.on("Quality Inspection", {
    setup: function (frm) {
        frm.set_query("item_code", function () {
            // Filter Items based on warehouse mentioned in QC Settings --> Default QC Processing Warehouse
            return {
                query: "mantra_dev.backend_code.api.get_items_from_warehouse",
            };
        });

        frm.set_query("item_serial_no", function () {
            if (!frm.doc.item_code) {
                frappe.msgprint(__("Please select an Item Code first."));
                return;
            }

            // Filter Item Serial No based on selected Item Code and warehouse mentioned in QC Settings --> Default QC Processing Warehouse
            return {
                query: "mantra_dev.backend_code.api.get_serial_nos",
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
                query: "mantra_dev.backend_code.api.get_quality_inspection_templates",
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
                query: "mantra_dev.backend_code.api.get_batch_nos",
                filters: {
                    item_code: doc.item_code,
                },
            };
        };
    },

    item_code: function (frm) {
        frm.set_value("item_serial_no", "")
        frm.set_value("batch_no", "")
        frm.set_value("sample_size", 0)

        // Fetch and Set Quality Inspection Template from Item master Quality Inspection Template field and accordingly set Readings child table on Item Code change
        if (frm.doc.item_code) {
            frm.set_value("item_serial_no", "")
            frm.set_value("batch_no", "")
            frm.set_value("sample_size", 0)

            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Item",
                    filters: { item_code: frm.doc.item_code },
                    fieldname: ["quality_inspection_template", "has_serial_no", "has_batch_no"]
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value("quality_inspection_template", r.message.quality_inspection_template || "");

                        if (r.message.quality_inspection_template == null) {
                            frm.clear_table("readings");
                            frm.refresh_field("readings");
                        }

                        if (r.message.has_batch_no && r.message.has_serial_no) {
                            frm.set_df_property("batch_no", "reqd", 1);
                            frm.set_df_property("item_serial_no", "reqd", 1);
                        } else if (r.message.has_batch_no) {
                            frm.set_df_property("batch_no", "reqd", 1);
                            frm.set_df_property("item_serial_no", "reqd", 0);
                        } else if (r.message.has_serial_no) {
                            frm.set_df_property("batch_no", "reqd", 0);
                            frm.set_df_property("item_serial_no", "reqd", 1);
                        } else {
                            frm.set_df_property("batch_no", "reqd", 0);
                            frm.set_df_property("item_serial_no", "reqd", 0);
                        }

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
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Serial No",
                    filters: { name: frm.doc.item_serial_no },
                    fieldname: "batch_no"
                },
                callback: function (r) {
                    if (r.message.batch_no) {
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
            frm.set_value("batch_no", "");
            frm.fields_dict.batch_no.get_query = function (doc) {
                // Filter Batch No based on selected Item Code and warehouse mentioned in QC Settings --> Default QC Processing Warehouse
                return {
                    query: "mantra_dev.backend_code.api.get_batch_nos",
                    filters: {
                        item_code: doc.item_code,
                    },
                };
            };
        }
    },


    batch_no: function (frm) {
        if (frm.doc.batch_no) {
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
                    query: "mantra_dev.backend_code.api.get_serial_nos",
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

        if (frm.doc.item_serial_no) {
            if (frm.doc.sample_size > 1) {
                frappe.msgprint(__("Sample Size cannot be more than 1 for serialized Item."));
                frm.set_value("sample_size", 1);
            }
        }

        else if (frm.doc.batch_no) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Batch",
                    filters: { name: frm.doc.batch_no },
                    fieldname: "batch_qty"
                },
                callback: function (r) {
                    if (r.message) {
                        const batch_qty = r.message.batch_qty;
                        if (frm.doc.sample_size > batch_qty) {
                            frappe.msgprint(__("Sample Size cannot exceed the batch quantity ({0}) in the warehouse.".replace("{0}", batch_qty)));
                            frm.set_value("sample_size", batch_qty);
                        }
                    }
                }
            })
        }

        else {

            // Sample Size can not exceed total No of Items in QC Settings --> Default QC Processing Warehouse
            frappe.call({
                method: "mantra_dev.backend_code.api.get_available_qty",
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
});