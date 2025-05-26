// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt


frappe.ui.form.on("QC Settings", {
    setup(frm) {
        frm.set_query("quality_manager", function() {
            return {
                query: "mantra_dev.mantra_dev.doctype.qc_settings.qc_settings.get_quality_managers",
                filters: {
                    role: "Quality Manager"
                }
            };
        });
    },
});
