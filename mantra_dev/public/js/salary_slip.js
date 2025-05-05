frappe.ui.form.on("Salary Slip", {
    refresh: function(frm) {

        if (["HR User","HR OPS User","HR OPS Manager","HR Manager"].some(role => frappe.user.has_role(role))) {
            frm.add_custom_button("Send salary slip mail", function() {
                frappe.call({
                    method: "mantra_dev.backend_code.salary_slip.employee_prefere_email_id",
                    args: {
                        employee: frm.doc.employee,
                    },
                    callback: function(r) {
                        if (r.message.status_code==200)
                        {
                            show_email_dialog(r.message.email,frm);
                        } 
                        else 
                        {
                            show_email_dialog("",frm);
                        }
                    },
                })
            }, "Utility");
        }
        

        if (["Accounts - Banking Manager"].some(role => frappe.user.has_role(role))) {
            // Check if status is Submitted (1) and payment status is not "Success"
            if (frm.doc.status == "Submitted" && frm.doc.custom_payment_status != "Success") {
                frm.add_custom_button("Mark as Paid", function() {                
                    show_payment_dialog(frm);
                }, "Utility");
            }
        }
    }
});

function show_payment_dialog(frm) {
    const today = frappe.datetime.get_today();

    const d = new frappe.ui.Dialog({
        title: 'Mark Salary Slip as Paid',
        fields: [
            {
                label: 'Liquidation Date',
                fieldname: 'liquidation_date',
                fieldtype: 'Date',
                default: today
            },
            {
                label: 'Instrument Ref No',
                fieldname: 'instrument_ref_no',
                fieldtype: 'Data',
            },
            {
                label: 'UTR NO',
                fieldname: 'utr_no',
                fieldtype: 'Data'
            },
            {
                label: 'Payment Ref No',
                fieldname: 'payment_ref_no',
                fieldtype: 'Data',
            },
            {
                label: 'Customer Ref No',
                fieldname: 'customer_ref_no',
                fieldtype: 'Data',
            },
            {
                label: 'Instrument No',
                fieldname: 'instrument_no',
                fieldtype: 'Data',
            }
        ],
        primary_action_label: 'Submit',
        primary_action(values) {

            frappe.call({
                method: 'mantra_dev.backend_code.salary_slip.mark_salary_slip_paid',
                args: {
                    salary_slip: frm.doc.name,
                    values: values
                },
                callback: function(res) {
                    console.log("Hello");
                    if (!res.exc) {
                        frappe.msgprint(res.message || "Payment details updated.");
                        frm.reload_doc();
                    }
                }
            });

            d.hide();
        }
    });

    d.show();
}

// Function to show dialog
function show_email_dialog(email,frm) {
    let d = new frappe.ui.Dialog({
        title: "Send Email",
        fields: [
            {
                label: "Email ID",
                fieldname: "email",
                fieldtype: "Data",
                default: email
            }
        ],
        primary_action_label: "Send",
        primary_action(values) {
            // if (!is_valid_email(values.email)) {
            //     frappe.msgprint({
            //         title: __("Invalid Email"),
            //         message: __("Please enter a valid email address."),
            //         indicator: "red"
            //     });
            //     return;
            // }

            frappe.call({
                method: "mantra_dev.backend_code.salary_slip.email_salary_slip_single_without_restriction",
                args: {
                    salary_slip_no: frm.doc.name,
                    prefered_email: values.email,
                },
                callback: function(r) {
                    frappe.msgprint(r.message.message);
                },
            })
            d.hide();
        }
    });
    d.show();
}
