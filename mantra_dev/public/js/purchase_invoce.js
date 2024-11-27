frappe.ui.form.on('Purchase Invoice', {
    onload (frm){
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
