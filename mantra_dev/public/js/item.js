frappe.ui.form.on('Item', {
    item_group(frm) {
        if (cur_frm.doc.item_group == "Services") {
            frm.set_value("is_stock_item", 0)
            cur_frm.set_df_property("is_stock_item", "read_only", 1)
        }
    },
    before_save(frm) {
        if (cur_frm.doc.item_group == "Services") {
            frm.set_value("is_stock_item", 0)
            cur_frm.set_df_property("is_stock_item", "read_only", 1)
        }
    }
})