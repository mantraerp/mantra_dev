frappe.ui.form.on('Project', {
    refresh: function(frm) {
        frm.add_custom_button(__('Calculate Project Qty'), function() {

            frappe.call({
                method: "mantra_dev.backend_code.project.project.get_sales_order_items",
                args: {
                    project: frm.doc.name
                },
                callback: function(response) {
                    if (response.message && response.message.length === 2) {
                        let aggregated_items = response.message[0]; 
                        let warehouse_list = response.message[1];
                        if (aggregated_items.length > 0) {
                            frappe.route_options = {
                                data: JSON.stringify(aggregated_items),  
                                warehouse: JSON.stringify(warehouse_list)  
                            }   
                        frappe.open_in_new_tab = true;
                        frappe.set_route('query-report', 'BOM Stock Calculated with Valuation rate');
                    }} else {
                        frappe.msgprint(__('No Sales Order Found for this Project'));
                    }     
            }
            });
        }, __('Utility'));}
});