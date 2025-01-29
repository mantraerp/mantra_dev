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

    before_save(frm) {
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
    }
});
