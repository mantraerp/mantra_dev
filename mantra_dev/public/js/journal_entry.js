frappe.ui.form.on('Journal Entry', {
	onload (frm){
        if(frm.is_new()){
            frm.set_query('voucher_type', () => {
                return {
                    filters: {
                        transaction_type: 'Journal Entry'
                    }
                };
            });
        }
    },
});