frappe.ui.form.on('Purchase Invoice', {
    onload (frm){

    // This added due to space not allow in supplier invoice number Jira - 343
        frm.fields_dict.bill_no.$wrapper.find('input').on('keypress', function(event) {

            if (event.which === 32) { // ASCII code for space
                event.preventDefault();
            }
        });
///////////////////////////////////

        if(frm.is_new()){
            frm.set_query('custom_invoice_type', () => {
                return {
                    filters: {
                        transaction_type: 'Purchase Invoice'
                    }
                }
            })
        }
        setTimeout(() => {
            frm.set_query('supplier', () => {
                return {
                    filters: {
                        workflow_state: 'Approved'
                    }
                };
            });
        }, 1000); // 
    },
    refresh(frm) {
        
        // if (frm.is_dirty()  && !frm.is_new()){

        //     frappe.call({
        //         method: "mantra_dev.backend_code.api.purchase_receipt_check_box",
        //         args: {
        //             invoice_name: frm.doc.name,
        //             invoice_docstatus: frm.doc.docstatus
        //         },
        //         callback: function (r) {
        //         }
        //     });
        // }
    },
    custom_department(frm){
        
        // frm.set_value("custom_expense_grouping","")
        // frm.fields_dict["custom_expense_grouping"].get_query = function () {
        //     let selected_department = frm.doc.custom_department;
        //     if (!selected_department) {
        //         return {};
        //     }
        //     return {
        //         filters: {
        //             name: ["in", get_selected_values(selected_department)]
        //         }
        //     };
        // };
    },
    before_save(frm) {

        // if(!frm.doc.custom_expense_grouping){
        //     frappe.throw("Please Select Department and Expense Grouping if it is not present Then tell Admin to Create Expense Grouping for that Department.")
        // }
        // if(!frm.doc.custom_department){
        //     frappe.throw("Please Select the Department")
        // }

        // If Item table present then check for linked PO no for purpose
        if (frm.doc.items && frm.doc.items.length > 0) {
            let purposes = [];
            let purchase_orders = [...new Set(frm.doc.items.map(item => item.purchase_order))]; 
            let promises = [];

            purchase_orders.forEach(purchase_order => {
                if (purchase_order) {
                    promises.push(
                        frappe.db.get_value('Purchase Order', purchase_order, 'custom_purpose').then(r => {
                            if (r.message && r.message.custom_purpose) {        
                                purposes.push(`${purchase_order}: ${r.message.custom_purpose}`);
                            }
                        })
                    );
                }
            });

            return Promise.all(promises).then(() => {
                // console.log("Final purposes: ", purposes);
                frm.set_value('custom_purpose', purposes.join('\n'));
                frm.refresh_field('custom_purpose');
            }).catch(err => {
                console.error("Error in promise resolution: ", err);
            });

        }
    },
    after_save(frm) {
        
        if(frm.doc.docstatus !== 2){
            frappe.call({
                method: "mantra_dev.backend_code.api.purchase_receipt_check_box_v1",
                args: {
                    invoice_name: frm.doc.name,
                    checkvalue:1
                },
                callback: function (r) {
                }
            });
        }

        if(frm.doc.payment_terms_template){
            frappe.call({
                method : 'mantra_dev.purchase_invoice.get_due_date_from_template',
                args:{
                    posting_date : frm.doc.posting_date,
                    bill_date : frm.doc.bill_date,
                    template_name: frm.doc.payment_terms_template
                },
                callback : function(r){
                    if(r.message){
                        let due_date = r.message
                        const payment_terms = cur_frm.doc.payment_schedule || [];
                        const promise = []
                        
                        payment_terms.forEach(row => {
                            promise.push(
                                frappe.db.set_value(row.doctype, row.name, "due_date", due_date)
                            );
                        });

                        Promise.all(promise).then(() => {
                            cur_frm.refresh_field("payment_terms");
                            frm.reload_doc();
                        }).catch(error => {
                            console.error("Error updating due dates:", error);
                        });
                    }
                }
            })
        }


        
        // let approvers = [
        //     frm.doc.custom_approver_1,
        //     frm.doc.custom_approver_2,
        //     frm.doc.custom_approver_3,
        //     frm.doc.custom_approver_4,
        //     frm.doc.custom_approver_5
        // ].filter(approver => approver)
        // console.log("----->",approvers);
        
        // if(approvers){

        //     frappe.call({
        //         method: "mantra_dev.backend_code.api.share_document",
        //         args: {
        //             doctype: "Purchase Invoice",
        //             name: frm.doc.name,
        //             users: approvers,
        //             read: 1,
        //             write: 1,
        //             share: 0,
        //             everyone: 0
        //         },
        //         callback(r) {
        //             if(r.message) {
        //                 console.log(r.message);
        //                 frm.reload_doc()
        //                 // document is shared with user
        //             }
        //         }
        //     })
        // }
    },
    after_workflow_action: function(frm) {

        if(frm.doc.docstatus === 2)
        {
            frappe.call({
                method: "mantra_dev.backend_code.api.purchase_receipt_check_box_v1",
                args: {
                    invoice_name: frm.doc.name,
                    checkvalue:0
                },
                callback: function (r) {
                }
            });
        }
    },
    validate(frm){
        
        // frappe.call({
        //     method: "mantra_dev.backend_code.api.get_verification_users",
        //     args: {
        //         expense_grouping_master: frm.doc.custom_expense_grouping,
        //         department: frm.doc.custom_department
        //     },
        //     callback: function(r) {
        //         if (r.message) {
        //         // Fill approver fields only if they are empty
        //         if (!frm.doc.custom_approver_1 || ""){
        //             frm.set_value("custom_approver_1", r.message[0][0] || "");
        //             frm.set_value("custom_approver_2", r.message[0][1] || "");
        //             frm.set_value("custom_approver_3", r.message[0][2] || "");
        //             frm.set_value("custom_approver_4", r.message[0][3] || "");
        //             frm.set_value("custom_approver_5", r.message[0][4] || "");
        //         } 
        //         // Find the last non-empty approver from the document fields
        //         let approvers = [
        //             frm.doc.custom_approver_1,
        //             frm.doc.custom_approver_2,
        //             frm.doc.custom_approver_3,
        //             frm.doc.custom_approver_4,
        //             frm.doc.custom_approver_5
        //         ];

        //         let last_approver = "";
        //         for (let i = approvers.length - 1; i >= 0; i--) { // Start from custom_approver_5 and go backwards
        //             if (approvers[i]) {
        //                 last_approver = approvers[i];
        //                 break;
        //             }
        //         }

        //         frm.set_value("custom_final_approver", last_approver);
        //         }else{
        //             // Find the last non-empty approver from the document fields
        //         let approvers = [
        //             frm.doc.custom_approver_1,
        //             frm.doc.custom_approver_2,
        //             frm.doc.custom_approver_3,
        //             frm.doc.custom_approver_4,
        //             frm.doc.custom_approver_5
        //         ];

        //         if(approvers=[] || !approvers){
        //             frappe.throw("There is no approver in verification flow and you have also not selected any approver.")
        //             return
        //         }

        //         let last_approver = "";
        //         for (let i = approvers.length - 1; i >= 0; i--) { // Start from custom_approver_5 and go backwards
        //             if (approvers[i]) {
        //                 last_approver = approvers[i];
        //                 break;
        //             }
        //         }

        //         frm.set_value("custom_final_approver", last_approver);

        //         }
        //     }
        // });
    },
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