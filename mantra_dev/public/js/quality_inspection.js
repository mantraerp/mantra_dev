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

        // Fetch and Set Quality Inspection Template from Item master Quality Inspection Template field and accordingly set Readings child table on Item Code change
        if (frm.doc.item_code) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Item",
                    filters: { item_code: frm.doc.item_code },
                    fieldname: "quality_inspection_template"
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value("quality_inspection_template", r.message.quality_inspection_template || "");


                        if (r.message.quality_inspection_template == null) {
                            frm.clear_table("readings");
                            frm.refresh_field("readings");
                        }
                    } else {
                        frm.set_value("quality_inspection_template", "");
                        frm.clear_table("readings");
                        frm.refresh_field("readings");
                    }
                }
            });
        } else {
            frm.set_value("quality_inspection_template", "");
            frm.clear_table("readings");
            frm.refresh_field("readings");
        }
    },

    sample_size: function (frm) {
        if (!frm.doc.item_code) {
            frappe.msgprint(__("Please select an Item Code first."));
            return;
        }

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
});
