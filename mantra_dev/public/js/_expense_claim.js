
frappe.ui.form.on("Expense Claim", {
    onload: function(frm) {
        // frm.set_df_property('expense_approver', 'read_only', 1)
        // frm.set_df_property('approval_status', 'hidden', 1)
        // make_expense_type_read_only(frm);
        
    },
    refresh(frm){
        // frm.set_df_property('expense_approver', 'read_only', 1)
        // frm.set_df_property('approval_status', 'hidden', 1)
        // make_expense_type_read_only(frm);
    },
    department(frm){
        // frm.fields_dict["custom_expense_grouping"].get_query = function () {
        //     let selected_department = frm.doc.department;
        //     if (!selected_department) {
        //         return {};
        //     }
        //     return {
        //         filters: {
        //             name: ["in", get_selected_values(selected_department)]
        //         }
        //     };
        // };
    },

    before_save(frm){
        // if (frm.doc.workflow_state !== "Rejected" && frm.doc.workflow_state !== "Cancelled"){
        //     frm.set_value("approval_status","Approved")
        // }
        // if(!frm.doc.department){
        //     frappe.throw("Please Select Employee or set the Department for the Employee")
        // }
        // if(!frm.doc.custom_expense_grouping){
        //     frappe.throw("Please Set the Expense Verification Flow for this Department")
        // }
        // frappe.call({
        //     method: "mantra_dev.backend_code.api.get_verification_users",
        //     args: {
        //         expense_grouping_master: frm.doc.custom_expense_grouping,
        //         department: frm.doc.department
        //     },
        //     callback: function(r) {
        //         if (r.message) {
        //             // console.log('---------------->',r.message);
        //             if(!frm.doc.custom_approver_1){
        //                 frm.set_value("custom_approver_1", r.message[0][0]);
        //             }
        //             if(!frm.doc.custom_approver_2){
        //                 frm.set_value("custom_approver_2", r.message[0][1]);
        //             }
        //             if(!frm.doc.custom_approver_3){
        //                 frm.set_value("custom_approver_3", r.message[0][2]);
        //             }
        //             if(!frm.doc.custom_approver_4){
        //                 frm.set_value("custom_approver_4", r.message[0][3]);
        //             }
        //             if(!frm.doc.custom_approver_5){
        //                 frm.set_value("custom_approver_5", r.message[0][4]);
        //             }
        //             let a1 = r.message[0].filter(function (e) {
        //                 return e; // Returns only the truthy values
        //             });
        //             x = a1.length
        //             frm.set_value("expense_approver", a1[x-1]);
        //         }
        //     }
        // });
    },

    after_save(frm){
        // let approvers = [
        //     frm.doc.custom_approver_1,
        //     frm.doc.custom_approver_2,
        //     frm.doc.custom_approver_3,
        //     frm.doc.custom_approver_4,
        //     frm.doc.custom_approver_5
        // ].filter(approver => approver)
        // console.log("----->",approvers);
        
        // if(approvers){

        //     frappe.call({
        //         method: "mantra_dev.backend_code.api.share_document",
        //         args: {
        //             doctype: "Expense Claim",
        //             name: frm.doc.name,
        //             users: approvers,
        //             read: 1,
        //             write: 1,
        //             share: 0,
        //             everyone: 0
        //         },
        //         callback(r) {
        //             if(r.message) {
        //                 console.log(r.message);
        //                 frm.reload_doc()
        //                 // document is shared with user
        //             }
        //         }
        //     })
        // }

    },

    before_workflow_action(frm){
        // if (frm.selected_workflow_action === 'Approve'){
            
        // }else{
        //     frappe.call({
        //         method: "mantra_dev.backend_code.api.expense_reject_status",
        //         args: {
        //             doc_name: frm.doc.name,
        //             status: "Rejected"
        //         },
        //         callback: function(r) {
        //             if (r.message) {
        //                console.log(r.message);
                       
        //             }
        //         }
        //     });
        // }
    },
    after_workflow_action(frm){
        // frappe.set_route("List", "Expense Claim");
    },
    custom_expense_grouping(frm){

        // frm.doc.expenses.forEach(row => {
        //     row.expense_type = frm.doc.custom_expense_grouping;
        // });
        // frm.refresh_field("expenses");
    },


})


frappe.listview_settings['Expense Claim'] = {
    onload: function (listview) {
        if (frappe.session.user !== "Administrator") {
            frappe.call({
                method: "mantra_dev.backend_code.api.get_user_expense_claims",
                args: {
                    user: frappe.session.user
                },
                async: false, // Ensure this runs before the list loads
                callback: function (r) {
                    let allowed_docnames = (r.message && r.message.length > 0) ? r.message : ["NoData"];
                    
                    // Set route options to apply filters before list loads
                    frappe.route_options = {
                        "name": ["in", allowed_docnames]
                    };

                    // Reload the page to apply the filters immediately before list fetch
                    frappe.set_route("List", "Expense Claim");
                }
            });
        } else {
            console.log("Session user is Administrator, showing all documents...");
        }
    }
};















// Trigger when a new row is added in the child table
frappe.ui.form.on("Expense Claim Detail", {
    expenses_add: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (frm.doc.custom_expense_grouping) {
            row.expense_type = frm.doc.custom_expense_grouping;
            frm.refresh_field("expenses");
        }
    },
    
});








function get_selected_values(department) {
    let selected_values = [];
    frappe.call({
        method: "frappe.client.get_list",
        async: false,
        args: {
            doctype: "Expense Verification Flow",
            filters: { select_department: department }, // Filter by selected department
            fields: ["select_expense_grouping"]
        },
        callback: function (r) {
            if (r.message) {
                selected_values = r.message.map(row => row.select_expense_grouping);
            }
        }
    });
    return selected_values;
}

function make_expense_type_read_only(frm) {
    if (frm.fields_dict["expenses"] && frm.fields_dict["expenses"].grid) {
        let grid = frm.fields_dict["expenses"].grid;
        
        // Use update_docfield_property to modify the child table field
        grid.update_docfield_property("expense_type", "read_only", 1);
        grid.update_docfield_property("expense_type", "hidden", 1);
        
        frm.refresh_field("expenses");
        console.log("Expense Type set to read-only.");
    } else {
        console.error("Child table 'expenses' not found or not loaded.");
    }
}




































// function disable_add_row(frm) {
    //     if (frm.fields_dict["expenses"] && frm.fields_dict["expenses"].grid) {
        //         frm.fields_dict["expenses"].grid.df.cannot_add_rows = true;
        //         frm.refresh_field("expenses");
        //         console.log("Add Row button disabled in 'expenses' child table.");
        //     } else {
            //         console.error("Child table 'expenses' not found or not loaded.");
            //     }
            // }
            
            
            // frappe.listview_settings['Expense Claim'] = {
            //     onload: function (listview) {
            //         function apply_filters() {
            //             if (frappe.session.user !== "Administrator") {
            //                 frappe.call({
            //                     method: "mantra_dev.backend_code.api.get_user_expense_claims",
            //                     args: {
            //                         user: frappe.session.user
            //                     },
            //                     async: false,
            //                     callback: function (r) {
            //                         let allowed_docnames = (r.message && r.message.length > 0) ? r.message : ["NoData"];
            
            //                         // Store the original get_args function
            //                         const original_get_args = listview.get_args;
            
            //                         listview.get_args = function () {
            //                             const args = original_get_args.apply(this);
            
            //                             // Ensure we maintain user-applied filters
            //                             if (!args.filters) {
            //                                 args.filters = [];
            //                             }
            
            //                             // Preserve any existing user filters but ensure document restriction
            //                             args.filters.push(["name", "in", allowed_docnames]);
            
            //                             return args;
            //                         };
            
            //                         listview.refresh();
            //                     }
            //                 });
            //             } else {
            //                 console.log("Session user is Administrator, showing all documents...");
            //             }
            //         }
            
            //         // Apply filters on list load
            //         apply_filters();
            
            //         // Ensure filters apply when returning from a document
            //         frappe.router.on("change", function () {
            //             if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "Expense Claim") {
            //                 apply_filters();
            //             }
            //         });
            
            //         // Ensure filters are re-applied when the user modifies filters in the UI
            //         listview.page.sidebar.find(".filter-selector").on("click", function () {
            //             setTimeout(apply_filters, 500); // Small delay to allow UI to update before applying filters
            //         });
            //     }
            // };
