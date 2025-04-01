// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.ui.form.on("Minop Setting", {
    setup : function(frm){
        frm.set_query('employee', function() {
            return {
                filters: {
                    status: 'Active' 
                }
            };
        });
    },
	// validate : function(frm){
    //     if(frm.doc.from_date && frm.doc.to_date){
    //         let from_date = frappe.datetime.str_to_obj(frm.doc.from_date);
    //         let to_date = frappe.datetime.str_to_obj(frm.doc.to_date);

    //         let difference = frappe.datetime.get_day_diff(to_date, from_date) + 1;
    //         console.log(difference)

    //         if (difference > 31){
    //             frappe.throw("Please select a date range of up to 31 days. Any range exceeding 31 days is not acceptable.")
    //         }
    //     }
    // },
    sync : function(frm){
        if (frm.is_dirty()) {
            frappe.throw('Please save the document first before processing.');
        }
        frm.call({
            method : 'get_attendance_process',
            args : {
                'fromdatetime': frm.doc.from_date,
                'todatetime' : frm.doc.to_date,
                'Emp_Code' : frm.doc.employee,
                'department':frm.doc.department
            },
            callback : function(r){
                console.log(r)
                if(r.message){
                   console.log(r)  
                }
                frappe.msgprint(r.message.message)
            }
        })
    }
});
