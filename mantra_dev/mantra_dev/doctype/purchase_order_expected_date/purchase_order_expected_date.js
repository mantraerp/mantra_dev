// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order Expected Date", {
	refresh(frm) {
        // If the form's status is 'Cancelled' or 'Received', disable the form to prevent edits
		if(frm.doc.status==='Cancelled' || frm.doc.status=='Received'){
            frm.disable_form()
		}
        // If the status is not 'Cancelled' and the received quantity is not equal to the expected quantity
		if(frm.doc.status!=='Cancelled' && frm.doc.qty !== frm.doc.received_qty){
            // Add a custom button "Split Qty" to the form
            frm.add_custom_button(__('Split Qty'), function() {
            var dialog = new frappe.ui.Dialog({
                title: __('Split Quantity'),
                fields: [
                    {
                        label: __('Qty to Split'),
                        fieldname: 'split_qty',
                        fieldtype: 'Float',
                        reqd: 1
                    }
                ],
                primary_action_label: __('Split'),
                primary_action(values) {
                  
                    let qty_to_split = values.split_qty;

                    if (!qty_to_split || qty_to_split <= 0) {
                        frappe.msgprint(__('Please enter a valid quantity.'));
                        return;
                    }
                    // Check if the split quantity exceeds the expected quantity
                    if (qty_to_split > frm.doc.expected_qty) {
                        frappe.msgprint(__('Entered quantity exceeds the original expected quantity.'));
                        return;
                    }

                    frm.call({
                        method: "split_qty_method",
                        args: {
                            docname: frm.doc.name,
                            qty_to_split: qty_to_split
                        },
                        callback: function(response) {
                            if (response.message) {
                                dialog.hide();
                                frm.reload_doc();
                            }
                        }
                    });
                }
            });

            dialog.show();
        });
		}
    },
	buffer_days(frm) {
        // Set the final expected receive date based on the updated date
    	if (frm.doc.expected_delivery_date && frm.doc.buffer_days) {
            let expected_delivery_date = frappe.datetime.str_to_obj(frm.doc.expected_delivery_date);
            expected_delivery_date.setDate(expected_delivery_date.getDate() + frm.doc.buffer_days);
            frm.set_value("final_expected_receive_date", frappe.datetime.obj_to_str(expected_delivery_date));
        }
		if (frm.doc.buffer_days == 0) {
            let expected_delivery_date = frappe.datetime.str_to_obj(frm.doc.expected_delivery_date);
            expected_delivery_date.setDate(expected_delivery_date.getDate());
            frm.set_value("final_expected_receive_date", frappe.datetime.obj_to_str(expected_delivery_date));
        }
    },
	expected_delivery_date(frm) {
        // Set the final expected receive date based on the updated date
       	if (frm.doc.expected_delivery_date || frm.doc.buffer_days) {
            let expected_delivery_date = frappe.datetime.str_to_obj(frm.doc.expected_delivery_date);
            expected_delivery_date.setDate(expected_delivery_date.getDate() + frm.doc.buffer_days);
            frm.set_value("final_expected_receive_date", frappe.datetime.obj_to_str(expected_delivery_date));
        }
	}

});