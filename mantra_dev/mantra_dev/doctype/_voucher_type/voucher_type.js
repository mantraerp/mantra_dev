// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.ui.form.on('Voucher Type', {
	onload (frm){
	    frm.set_df_property('transaction_type', 'only_select', true);
        if(frm.is_new()){
            frm.set_query('transaction_type', () => {
                return {
                    filters: {
                        name: ['in',['Purchase Invoice','Sales Invoice','Journal Entry']]
                    }
                };
            });
        }
    },
});
