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

		frm.add_custom_button(("Send Attendance Summery Mail"), () => {
			let d = new frappe.ui.Dialog({
				title: "Send Attendance Summery Mail",
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
				primary_action_label: "Send Mail",
				primary_action(values) {
					if (values.from_date && values.to_date) {
						let from_date = new Date(values.from_date);
						let to_date = new Date(values.to_date);

						if (to_date < from_date) {
							frappe.throw({
								title: __("Validation Error"),
								message: __("To Date cannot be earlier than From Date."),
							});
						}
						frappe.call({
							method: "mantra_dev.mantra_dev.report.employee_attendance_summery.employee_attendance_summery.send_employee_attendace_summery_report_mail",
							args: { 
								filters: {
									from_date: values.from_date,
									to_date: values.to_date,
									employee : frm.doc.name
								}
							},
							freeze: true,
							freeze_message: "sending data...",
							callback: function (r) {
								if(r.message){
									frappe.dom.unfreeze();
									d.hide();
									frappe.msgprint(r.message)
								}
								else{
									frappe.msgprint(r.message);
								}
							}
						});
					} else {
						frappe.throw("Please Select Both Date.")
					}
				}
			})

			d.show();
		
		}, ('Utility'));
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
	},
	validate(frm) {
		const nameRegex = /^[A-Za-z\s]+$/;
		const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
 
		const first_name = frm.doc.first_name;
		const middle_name = frm.doc.middle_name;
		const last_name = frm.doc.last_name;
		const cell = frm.doc.cell_number;
		const personal_email = frm.doc.personal_email;
		const company_email = frm.doc.company_email;
		const pan = frm.doc.pan_number;
		const pf_account = frm.doc.provident_fund_account;
		const ifsc_code = frm.doc.ifsc_code;
		const esic = frm.doc.custom_esic_no;
		const uan = frm.doc.custom_uan_no;
		const passport = frm.doc.passport_number;
 
		if (first_name && !nameRegex.test(first_name)) {
			frappe.throw(__("First Name must contain only letters and space."));
		}
 
		if (middle_name && !nameRegex.test(middle_name)) {
			frappe.throw(__("Middle Name must contain only letters and space."));
		}
 
		if (last_name && !nameRegex.test(last_name)) {
			frappe.throw(__("Last Name must contain only letters and space."));
		}
 
		if (cell) {
			const cellRegex = /^\d{10}$/;
			if (!cellRegex.test(cell)) {
				frappe.throw(
					__("Invalid Mobile Number. It must be exactly 10 digits.")
				);
			}
		}
 
		if (personal_email && !emailRegex.test(personal_email)) {
			frappe.throw(__("Invalid Personal Email."));
		}
 
		if (company_email && !emailRegex.test(company_email)) {
			frappe.throw(__("Invalid Company Email."));
		}
 
		if (pan) {
			const panRegex = /^[A-Z]{5}(?!0{4})[0-9]{4}[A-Z]{1}$/;
			if (!panRegex.test(pan)) {
				frappe.throw(
					__(
						"Invalid PAN Number. Format: 5 uppercase letters, 4 digits (not all zeros), and 1 uppercase letter."
					)
				);
			}
		}
 
		if (pf_account) {
			const pfRegex = /^[A-Za-z0-9]{22}$/;
			if (!pfRegex.test(pf_account)) {
				frappe.throw(
					__(
						"Invalid Provident Fund Account. It must be exactly 22 letters or digits."
					)
				);
			}
		}
 
		if (ifsc_code) {
			const ifscRegex = /^[A-Z]{4}0[A-Z0-9]{6}$/;
			if (!ifscRegex.test(ifsc_code)) {
				frappe.throw(
					__(
						"Invalid IFSC Code. Format: 4 letters, 0, then 6 alphanumeric characters. Example: SBIN0001234"
					)
				);
			}
		}
 
		if (esic) {
			const esicRegex = /^\d{10}$/;
			if (!esicRegex.test(esic)) {
				frappe.throw(__("Invalid ESIC Number. It must be exactly 10 digits."));
			}
		}
 
		if (uan) {
			const uanRegex = /^\d{12}$/;
			if (!uanRegex.test(uan)) {
				frappe.throw(__("Invalid UAN Number. It must be exactly 12 digits."));
			}
		}
 
		if (passport) {
			const passportRegex = /^[A-Z][0-9]{7}$/;
			if (!passportRegex.test(passport)) {
				frappe.throw(
					__(
						"Invalid Passport Number. It should be 1 letter followed by 7 digits. Example: A1234567"
					)
				);
			}
		}
	},
})