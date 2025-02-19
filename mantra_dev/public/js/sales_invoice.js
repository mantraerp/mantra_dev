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

            if (frm.doc.custom_sales_person) 
            {
                // alert('call');

                frappe.call({
                    method: 'frappe.client.get_value',
                    args: {
                        doctype: 'Sales Person',
                        name: frm.doc.custom_sales_person,
                        fieldname: 'custom_bank_account'
                    },
                    callback: function(r){ 
                        frm.set_value("custom_bank_account", r.message.custom_bank_account);
                    }
                });
            }
        }


        

        // alert('temp');
    },

    
    on_submit(frm){
        frappe.call({
            method: "mantra_dev.backend_code.api.create_delivery_note",
            args: {
                data: frm.doc,
            },
            callback: function(r) {
                // console.log('lllllllllllll');
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