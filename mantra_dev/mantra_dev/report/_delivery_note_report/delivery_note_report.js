frappe.query_reports["Delivery Note Report"] = {
    "filters": [
        {
            "fieldname": "customer",
            "label": "Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 300
        },
        {
            "fieldname": "custom_sales_invoice_no",
            "label": __("Sales Invoice"),
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 300
        }
    ],
	onload: function(report) {
        // frappe.query_report.set_filter_value('from_date', frappe.datetime.month_start());
        // frappe.query_report.set_filter_value('to_date', frappe.datetime.month_end());
        
        $(document).on('click', '.create-shipment', function() {
            var data = $(this).data();
            var delivery_note_no = data.id;
			
			console.log(data); // Log the data attributes for debugging
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
						default:delivery_note_no,
						read_only:1,
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
            d.show();
        });
	},
	formatter: function(value, row, column, data, default_formatter) {
			if (column.fieldname == "shipment") {
				return value;
			}
			return default_formatter(value, row, column, data);
	}
}