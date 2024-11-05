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
});