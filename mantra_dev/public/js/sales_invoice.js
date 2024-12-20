frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {       
        setTimeout(() => {
            frm.set_query('customer', () => {
                return {
                    filters: {
                        workflow_state: 'Approved'
                    }
                };
            });
        }, 1000); // 1000 milliseconds = 1 second              
    },
    onload (frm){
        if(frm.is_new()){
            frm.set_query('custom_invoice_type', () => {
                return {
                    filters: {
                        transaction_type: 'Sales Invoice'
                    }
                };
            });
        }
    },

    
    on_submit(frm){
        frappe.call({
            method: "mantra_dev.backend_code.api.create_delivery_note",
            args: {
                data: frm.doc,
            },
            callback: function(r) {
                console.log('lllllllllllll');
            }
        });
    },

    
    einvoice_status(frm){
        frappe.call({
            method: "mantra_dev.backend_code.api.create_delivery_note",
            args: {
                data: frm.doc,
            },
            callback: function(r) {
                console.log('dsfgsdfsdf');
            }
        });
    },

    
});

// frappe.ui.form.on("Sales Invoice Item", "items", function(frm, cdt, cdn) {
//     var d = locals[cdt][cdn];
//     if (frm.doc.is_return == 0 || frm.doc.update_outstanding_for_self == 0){
//         setTimeout(() => {
//         	d.income_account = frm.doc.custom_income_account;
//         	frm.refresh_field('item');
//         }, 1000); // 1000 milliseconds = 1 second 
//     }
// });