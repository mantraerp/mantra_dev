frappe.ui.form.on('Employee', {
	refresh(frm) {

        frm.add_custom_button(("Send salary slip mail"), () => {

			
				let dialog = new frappe.ui.Dialog({
					title: "Select Date Range",
					fields: [
						{
							label: "From Date",
							fieldname: "from_date",
							fieldtype: "Date",
							reqd: 1
						},
						{
							label: "To Date",
							fieldname: "to_date",
							fieldtype: "Date",
							reqd: 1
						}
					],
					primary_action_label: "Submit",
					primary_action(values) {
						if (values.from_date && values.to_date) {
							
						
								frappe.call({
									method: "mantra_dev.backend_code.salary_slip.salary_slip_date_range",
									args: { 
										from_date: values.from_date,
										to_date: values.to_date,
										employee_id : frm.doc.name
									},
									freeze: true,
									freeze_message: "finding data...",
									callback: function (r) {
										if(r.message.status_code===200)
										{
											frappe.confirm(r.message.message,
												() => {
													// action to perform if Yes is selected
													frappe.msgprint("Email sending process start in background.");
													frappe.call({
														method: "mantra_dev.backend_code.salary_slip.salary_slip_date_range_back",
														args: { 
															from_date: values.from_date,
															to_date: values.to_date,
															employee_id : frm.doc.name
														 },
														callback: function (r) {
														}
													});
					
												}, () => {
													// action to perform if No is selected
												})
										}
										else{
											frappe.msgprint(r.message.message);
										}
									}
								});
	
							// Add logic here (e.g., make an API call, filter data, etc.)
						} else {
							frappe.msgprint("Please select both dates.");
						}
						dialog.hide();
					}
				});
			
				// Show the dialog
				dialog.show();
        },('Utility'));
    },
	department(frm) {
	    frm.set_value("custom_opration_approver",undefined)
	    frappe.call({
	        method:"mantra_dev.backend_code.api.get_opration_approver",
	        args:
	        {
	           department :cur_frm.doc.department,
	        },
	       callback: function(r) {
	            // alert(r.message)
	            // if (r.message.length!=0){
	                setTimeout(() => {
                        frm.set_query('custom_opration_approver', () => {
                            return {
                                filters: {
                                    name: ["in",r.message]
                                }
                            };
                        });
                    }, 1000); // 
    // },
	            // }	            
	       }	        
	    })
	}
})