frappe.ui.form.on('Purchase Receipt', {
    onload(frm) {
        frm.set_query('set_warehouse', () => {
            return {
                filters: {
                    custom_is_purchase_warehouse: 1
                }
            };
        });
        frm.set_query('rejected_warehouse', () => {
            return {
                filters: {
                    custom_is_purchase_warehouse: 1
                }
            };
        });
        setTimeout(() => {
            frm.set_query('supplier', () => {
                return {
                    filters: {
                        workflow_state: 'Approved'
                    }
                };
            });
        }, 1000); // 1000 milliseconds = 1 second    
    }
});