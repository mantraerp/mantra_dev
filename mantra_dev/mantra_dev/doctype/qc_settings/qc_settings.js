// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt


frappe.ui.form.on("QC Settings", {
    setup(frm) {
        frm.set_query("default_inward_warehouse", function () {
            const default_company = frappe.defaults.get_default("company");
            return {
                filters: {
                    company: default_company,
                    is_group: 0,
                }
            };
        });


        frm.set_query("default_qc_accepted_warehouse", function () {
            const default_company = frappe.defaults.get_default("company");
            return {
                filters: {
                    company: default_company,
                    is_group: 0,
                }
            };
        });


        frm.set_query("default_qc_processing_warehouse", function () {
            const default_company = frappe.defaults.get_default("company");
            return {
                filters: {
                    company: default_company,
                    is_group: 0,
                }
            };
        });


        frm.set_query("default_qc_rejected_warehouse", function () {
            const default_company = frappe.defaults.get_default("company");
            return {
                filters: {
                    company: default_company,
                    is_group: 0,
                }
            };
        });
    },
});
