frappe.ui.form.on('Delivery Note', {
    onload(frm) {
        frm.set_query('set_warehouse', () => {
            return {
                filters: {
                    custom_is_sales_warehouse: 1
                }
            };
        });
        setTimeout(() => {
            frm.set_query('customer', () => {
                return {
                    filters: {
                        workflow_state: "Approved",
                    }
                };
            });
        }, 1000); // 1000 milliseconds = 1 second   
        frm.set_query('set_target_warehouse', () => {
            return {
                filters: {
                    custom_is_sales_warehouse: 1
                }
            };
        });
    },
    before_save: function (frm) {
        frm.doc.items.forEach((item, index) => {
            if (item.against_sales_invoice) {
                // Additional specific condition
                console.log('Item against sales invoice:', item.against_sales_invoice);
            } else {
                if (item.against_sales_order) {
                    console.log(item.base_amount);
                    if (parseInt(item.base_amount) > 0) {
                        frappe.throw(`You cannot create a delivery note with an amount of more than 0. Please remove line item ${item.idx} from the delivery note.`);
                    } else {
                        console.log('Item against sales order:', item.against_sales_order);
                    }
                }
            }
            if(frm.doc.is_return!=1){
                if (item.serial_no) {
                    var ser = item.serial_no;
                    console.log(ser)
                    var a = ser.split('\n');
                    console.log(a,"jvnhhgn")
                    cleaned_list = a.filter(item => item !== '');
                    console.log(cleaned_list,"ssss")
                    console.log(cleaned_list.length)
                //     var serial_no_list = [];
                    if(item.qty!=cleaned_list.length){
                        frappe.throw("Item Actual Qty & Total Serial No which you scan are does not match")
                    }
                    // // Loop through the serial numbers up to the minimum of qty and the length of a
                    // for (var i1 = 0; i1 < item.qty; i1++) {
                    //     serial_no_list.push(a[i1]);
                    // }
                    // // Join the serial numbers with newline characters
                    // console.log(serial_no_list)
                    // item.serial_no = serial_no_list.join("\n");
                    // item.custom_qr = undefined;
                    // // Refresh the field to reflect the changes
                    frm.refresh_field("items");
                    // Log the length of the serial number list
                    console.log(a.length);
                }
            }
        });
         
    }

});
frappe.listview_settings['Delivery Note'] = {
    onload: function(listview) {
        // Add button to create shipment
        listview.page.add_inner_button(__('Create Shipment'), function() {
            // Define the dialog
            let d = new frappe.ui.Dialog({
                title: 'Shipment Form',
                fields: [
                    {
                        fieldtype: 'Section Break',
                        label: 'Shipment Details'
                    },
                    {
                        label: 'Delivery Note ID',
                        fieldname: 'dc_id',
                        fieldtype: 'Link',
                        options: "Delivery Note",
                        reqd: 1,
                        get_query: function() {
                            return {
                                filters: [
                                    ['Delivery Note', 'docstatus', '=', 1]
                                ]
                            };
                        }
                    },
                    {
                        label: 'Service Provider',
                        fieldname: 'service_provider',
                        fieldtype: 'Data',
                        reqd: 1,
                    },
                    {
                        fieldtype: 'Column Break'
                    },
                    {
                        label: 'AWB Number',
                        fieldname: 'awb_number',
                        fieldtype: 'Data',
                        reqd: 1,
                    },
                    
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    console.log(values);
                    // Add code to handle the submission
                    frappe.call({
                        method: "mantra_dev.backend_code.api.create_shipment",
                        args: {
                            values: values,
                            delivery_note_id: values.dc_id,
                            service_provider: values.service_provider,
                            awb_number: values.awb_number,
                            attachment: values.attachment,
                            pickup_from: values.pickup_from,
                            pickup_to: values.pickup_to,
                            shipment_parcel: values.shipment_parcel
                        },
                        callback: function(response) {
                            if (response.message) {
                                frappe.msgprint(__('Shipment created successfully!'));
                            } else {
                                frappe.msgprint(__('An error occurred while creating the shipment.'));
                            }
                        }
                    });
                    d.hide();
                }
            });

            // Show the dialog
            d.show();
        });

        // Apply filter to show only completed delivery notes
        listview.filter_area.add([
            ["Delivery Note", "status", "=", "Completed"]
        ]);
    }
};
