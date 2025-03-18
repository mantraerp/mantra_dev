frappe.ui.form.on("Salary Slip", {
    refresh: function(frm) {
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
});

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

            // console.log("GGGGGGGGGGGGGGGGGGGG");
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
