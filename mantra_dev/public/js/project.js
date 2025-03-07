frappe.ui.form.on('Project', {
    refresh: function(frm) {
        frm.add_custom_button(__('Calculate Project Qty'), function() {

            frappe.call({
                method: "mantra_dev.backend_code.project.project.get_sales_order_items",
                args: {
                    project: frm.doc.name
                },
                callback: function(response) {
                    console.log(response.message)
                    if (response.message && response.message.length === 2) {
                        let aggregated_items = response.message[0]; 
                        if (aggregated_items.length > 0) {
                            frappe.route_options = {
                                data: JSON.stringify(aggregated_items)
                            }   
                        frappe.open_in_new_tab = true;
                        frappe.set_route('query-report', 'Project Tracking');
                    }} else {
                        frappe.msgprint(__('No Sales Order Found for this Project'));
                    }     
            }
            });
        }, __('Utility'));
    
    }
});