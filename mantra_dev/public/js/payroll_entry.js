frappe.ui.form.on("Payroll Entry", {
    refresh(frm) {

        frm.add_custom_button(("Send salary slip mail"), () => {
            frappe.call({
                method: "mantra_dev.backend_code.salary_slip.email_payroll_salary_slip",
                args: { payroll_no: frm.doc.name },
                freeze: true,
                freeze_message: "finding data...",
                callback: function (r) {
                    if(r.message.status_code===200)
                    {
                        frappe.confirm(r.message.message,
                            () => {
                                // action to perform if Yes is selected
                                frappe.msgprint("Email sending process start in background.");
                                frappe.call({
                                    method: "mantra_dev.backend_code.salary_slip.email_payroll_salary_slip_back",
                                    args: { payroll_no: frm.doc.name },
                                    callback: function (r) {
                                    }
                                });

                            }, () => {
                                // action to perform if No is selected
                            })
                    }
                    else{
                        frappe.msgprint(r.message.message);
                        // frappe.msgprint('ravi');
                    }
                }
            });
        },('Utility'));

        if (frappe.user.has_role("Accounts - Banking Manager")) {
            frm.add_custom_button(("Create payment entry file"), () => {

                    var d = new frappe.ui.Dialog({
                        title: __("Payroll payment entry"),
                        primary_action_label: __("close"),
                        primary_action: () => {
        
                            // frappe.warn('Are you sure you want to proceed?',
                            //     'This will create payroll payment entry in bank.',
                            //     () => {
                            //         // action to perform if Continue is selected
                            //         frappe.call({
                            //             method: "mantra_dev.api_code.banck_transaction.generate_payroll_payment_file",
                            //             args: { 
                            //                 payroll_entry: frm.doc.name,
                            //                 create_only_file:0
                            //             },
                            //             freeze: true,
                            //             freeze_message: "Please wait...",
                            //             callback: function (r) {
                        
                            //                 if(r.message.status_code===200)
                            //                 {
                            //                     frm.reload_doc();
                            //                 }
                                            
                            //                 frappe.msgprint(r.message.message);
                            //             }
                            //         });
                            //     },
                            //     'Continue',
                            //     true // Sets dialog as minimizable
                            // )
                            d.hide();
                        },
                        secondary_action_label: __("Check payment file"),
                        secondary_action: () => {
                            frappe.call({
                                method: "mantra_dev.api_code.banck_transaction.generate_payroll_payment_file",
                                args: { 
                                    payroll_entry: frm.doc.name,
                                    create_only_file:1
                                },
                                freeze: true,
                                freeze_message: "Please wait...",
                                callback: function (r) {
                
                                    if(r.message.status_code===200)
                                    {
                                        frm.reload_doc()
                                    }
                                    
                                    frappe.msgprint(r.message.message);
                                }
                            });
                            d.hide();
                        }
                    });
                    
                    d.$body.append(`<p class="frappe-confirm-message">${'Are you sure you want to process for payment entry or check payment file first ?'}</p>`);
                    d.show();
                    return;
                


                

            },('Utility'));
        }



    //     return;

    //     if (frm.doc.custom_salary_slip_file_generated === 1 && frm.doc.docstatus === 1){
    //         if (frm.custom_buttons) frm.clear_custom_buttons();
    //     }else{
    //         frm.doc.custom_salary_slip_file_generated = 0
    //     }

    //     if (frm.doc.docstatus === 0 && !frm.is_new()) {
    //         if (frm.custom_buttons) frm.clear_custom_buttons();
    //     }

    //     // Check if both Journal Entries are submitted
    //     frappe.call({
    //         method: "frappe.client.get_list",
    //         args: {
    //             doctype: "Journal Entry",
    //             filters: [
    //                 ["Journal Entry Account", "reference_name", "=", frm.doc.name],
    //                 ["docstatus", "=", 1]
    //             ],
    //             fields: ["name"],
    //             distinct: true
    //         },
    //         callback: function (r) {
    //             // console.log(r);
    //             if (r.message && r.message.length === 2) {
    //                 console.log(r);
    //                 frappe.call({
    //                     method: "frappe.client.get_list",
    //                     args: {
    //                         doctype: "File",
    //                         filters: {
    //                             "attached_to_doctype": "Payroll Entry",
    //                             "attached_to_name": frm.doc.name,
    //                             "file_name": ["like", "MANTRASH2H_MANTRASH2HUP%"]
    //                         },
    //                         fields: ["file_name"]
    //                     },
    //                     callback: function (res) {
    //                         console.log(res);
    //                         // If file exists, hide the button
    //                         if (res.message && res.message.length > 0) {
    //                             if (frm.custom_buttons) frm.clear_custom_buttons();
    //                             // console.log(res.message);
    //                             return;  
    //                         } else {
    //                             frm.events.add_context_buttons(frm); 
    //                         }
    //                     }
    //                 });
    //             }
    //         }
    //     });
    },

    // add_context_buttons(frm) {

    //     frm.add_custom_button("Generate Salary-Slip", function () {
    //         // frappe.call({
    //         //     method: "mantra_dev.api_code.banck_transaction.generate_salary_slip",
    //         //     args: { payroll_entry: frm.doc.name },
    //         //     callback: function (r) {
    //         //         console.log(r);
    //         //         frm.reload_doc()
    //         //         if (r.message && r.message.startsWith("File created successfully")) {
    //         //             frappe.msgprint(r.message);
    //         //             frm.remove_custom_button("Generate Salary-Slip.txt");
    //         //         } else {
    //         //             frappe.msgprint({
    //         //                 title: "Error",
    //         //                 message: r.message || "File generation failed!",
    //         //                 indicator: "red"
    //         //             });
    //         //         }
    //         //     }
    //         // });
    //     });
    // }
});