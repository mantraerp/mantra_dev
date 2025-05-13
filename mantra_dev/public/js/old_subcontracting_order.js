frappe.ui.form.on('Subcontracting Order', {
    onload(frm) {
        frm.set_query('supplier_warehouse', () => {
            return {
                filters: {
                    custom_is_subcontracting_warehouse: 1
                }
            };
        });
        frm.set_query('set_warehouse', () => {
            return {
                filters: {
                    custom_is_purchase_warehouse: 1
                }
            };
        });
        frm.set_query("set_reserve_warehouse", () => {
			return {
				filters: {
					company: frm.doc.company,
					// name: ["!    =", frm.doc.supplier_warehouse],
					is_group: 0,
				},
			};
		});
    }
});