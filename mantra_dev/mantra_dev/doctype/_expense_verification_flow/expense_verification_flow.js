// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Verification Flow", {
	refresh(frm) {

	},
    approver_role_1: function(frm) {
        if (frm.doc.approver_role_1) {
            frm.set_value("verifier", "");
        }
    },
    verifier: function(frm) {
        if (frm.doc.verifier) {
            frm.set_value("approver_role_1", "");
        }
    },
    approver_role_2: function(frm) {
        if (frm.doc.approver_role_2) {
            frm.set_value("approver", "");
        }
    },
    approver: function(frm) {
        if (frm.doc.approver) {
            frm.set_value("approver_role_2", "");
        }
    },
    approver_role_3: function(frm) {
        if (frm.doc.approver_role_3) {
            frm.set_value("validation_1", "");
        }
    },
    validation_1: function(frm) {
        if (frm.doc.validation_1) {
            frm.set_value("approver_role_3", "");
        }
    },
    approver_role_4: function(frm) {
        if (frm.doc.approver_role_4) {
            frm.set_value("validation_2", "");
        }
    },
    validation_2: function(frm) {
        if (frm.doc.validation_2) {
            frm.set_value("approver_role_4", "");
        }
    },
    approver_role_5: function(frm) {
        if (frm.doc.approver_role_5) {
            frm.set_value("auditor", "");
        }
    },
    auditor: function(frm) {
        if (frm.doc.auditor) {
            frm.set_value("approver_role_5", "");
        }
    },


    select_department(frm) {
        frm.set_value("select_expense_grouping","")
        frm.fields_dict["select_expense_grouping"].get_query = function () {
            let selected_department = frm.doc.select_department;
            if (!selected_department) {
                return {};
            }
            return {
                filters: {
                    name: ["not in", get_selected_values(selected_department)]
                }
            };
        };
    },
    before_save(frm){
        // if(!frm.doc.verifier && !frm.doc.approver_role_1){
        //     frappe.throw("Please give one approver User or Role");
        //     // return false
        // }
        // let fields = ["verifier", "approver", "validation_1", "validation_2", "auditor"];
        // let last_filled_index = -1;  // Track the last filled field index

        // for (let i = 0; i < fields.length; i++) {
        //     if (frm.doc[fields[i]]) {
        //         // If a field is filled after an empty one, clear it
        //         if (last_filled_index !== -1 && i > last_filled_index + 1) {
        //             // frappe.msgprint(`Skipping fields is not allowed. Clearing "${fields[i]}"`);
        //             frm.set_value(fields[i], "");  // Clear the incorrect field
        //         } else {
        //             last_filled_index = i;  // Update last filled index
        //         }
        //     }
        // }
    }
});



function get_selected_values(department) {
    let selected_values = [];
    frappe.call({
        method: "frappe.client.get_list",
        async: false,
        args: {
            doctype: "Expense Verification Flow",
            filters: { select_department: department }, // Filter by selected department
            fields: ["select_expense_grouping"]
        },
        callback: function (r) {
            if (r.message) {
                selected_values = r.message.map(row => row.select_expense_grouping);
            }
        }
    });
    return selected_values;
}
