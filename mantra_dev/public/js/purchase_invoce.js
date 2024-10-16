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
        frappe.call({
            method: "mantra_dev.backend_code.api.purchase_receipt_check_box",
            args: {
                invoice_name: frm.doc.name,
                invoice_docstatus: frm.doc.docstatus
            },
            callback: function (r) {
            }
        });
    },
});
