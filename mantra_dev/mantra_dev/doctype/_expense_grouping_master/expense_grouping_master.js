// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Grouping Master", {
	refresh(frm) {

	},
    after_save(frm){
        frappe.call({
            method: "mantra_dev.backend_code.api.create_new_expense_type",
            args: {
                name: frm.doc.name,
            },
            callback(r) {
                if(r.message) {
                    console.log(r.message);
                    // document is shared with user
                }
            }
        })
    },
});
