frappe.ui.form.on('Tax Category', {
    onload(frm, cdt, cdn) {
        frm.set_query('income_account', 'custom_account_default', function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: {
                    is_group: 0,
                    company: d.company
                }
            };
        });
        frm.set_query('export_sales_account', 'custom_account_default', function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: {
                    is_group: 0,
                    company: d.company
                }
            };
        });
    }
});