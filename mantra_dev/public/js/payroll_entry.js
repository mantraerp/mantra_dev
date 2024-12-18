frappe.ui.form.on("Payroll Entry", {
    refresh(frm) {

        if (frm.doc.custom_salary_slip_file_generated === 1 && frm.doc.docstatus === 1){
            if (frm.custom_buttons) frm.clear_custom_buttons();
        }else{
            frm.doc.custom_salary_slip_file_generated = 0
        }

        // if (frm.doc.docstatus === 0 && !frm.is_new()) {
        //     if (frm.custom_buttons) frm.clear_custom_buttons();
        // }

        // Check if both Journal Entries are submitted
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Journal Entry",
                filters: [
                    ["Journal Entry Account", "reference_name", "=", frm.doc.name],
                    ["docstatus", "=", 1]
                ],
                fields: ["name"],
                distinct: true
            },
            callback: function (r) {
                // console.log(r);
                if (r.message && r.message.length === 2) {
                    console.log(r);
                    frappe.call({
                        method: "frappe.client.get_list",
                        args: {
                            doctype: "File",
                            filters: {
                                "attached_to_doctype": "Payroll Entry",
                                "attached_to_name": frm.doc.name,
                                "file_name": ["like", "MANTRASH2H_MANTRASH2HUP%"]
                            },
                            fields: ["file_name"]
                        },
                        callback: function (res) {
                            console.log(res);
                            // If file exists, hide the button
                            if (res.message && res.message.length > 0) {
                                if (frm.custom_buttons) frm.clear_custom_buttons();
                                console.log(res.message);
                                return;  
                            } else {
                                frm.events.add_context_buttons(frm); 
                            }
                        }
                    });
                }
            }
        });
    },

    add_context_buttons(frm) {

        frm.add_custom_button("Generate Salary-Slip.txt", function () {
            frappe.call({
                method: "mantra_dev.api_code.banck_transaction.generate_salary_slip",
                args: { payroll_entry: frm.doc.name },
                callback: function (r) {
                    console.log(r);
                    frm.reload_doc()
                    // if (r.message && r.message.startsWith("File created successfully")) {
                    //     frappe.msgprint(r.message);
                    //     frm.remove_custom_button("Generate Salary-Slip.txt");
                    // } else {
                    //     frappe.msgprint({
                    //         title: "Error",
                    //         message: r.message || "File generation failed!",
                    //         indicator: "red"
                    //     });
                    // }
                }
            });
        });
    }
});