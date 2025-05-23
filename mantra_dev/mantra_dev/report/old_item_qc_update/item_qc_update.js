// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Item QC Update"] = {
	onload: function (report) {
        $(document).on("click", ".update-qc", function () {
            let item_code = $(this).data("item");

            frappe.prompt([
                {
                    label: "Quality Inspection Template",
                    fieldname: "quality_inspection_template",
                    fieldtype: "Link",
                    options: "Quality Inspection Template",
                },
                {
                    label: "Inspection Required Before Transfer Warehouse",
                    fieldname: "inspection_required",
                    fieldtype: "Check",
                }
            ], function (values) {

                if (values.inspection_required && !values.quality_inspection_template) {
                    frappe.msgprint({
                        title: __("Validation Error"),
                        indicator: "red",
                        message: __("Quality Inspection Template is required when Inspection Required is checked.")
                    });
                    return;
                }

                frappe.call({
                    method: "mantra_dev.mantra_dev.report.item_qc_update.item_qc_update.update_qc_template",
                    args: {
                        item_code: item_code,
                        template: values.quality_inspection_template || null,
                        inspection_required: values.inspection_required ? 1 : 0
                    },
                    callback: function () {
                        frappe.msgprint(`QC Template and Inspection Required flag updated for <b>${item_code}</b>.`);
                        report.refresh();
                    }
                });
            }, "Update Quality Inspection");
        });

        setTimeout(() => {
            $('.dropdown-menu li:contains("Add Column")').hide();
        }, 500);
    }
};
