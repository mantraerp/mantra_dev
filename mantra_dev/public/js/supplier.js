frappe.ui.form.on("Supplier", {

    onload(frm){
        // if(frm.doc.workflow_state === 'Approved'){
        //     frm.set_df_property('custom_add_bank_account', 'hidden', 0);
        // }
    },
    
    refresh(frm){
        if(frm.is_new()){

            frm.set_df_property('custom_add_bank_account', 'hidden', 1);
            frm.set_df_property('custom_bank_account_table', 'read_only', 0);
        }else{            
            frm.set_df_property('custom_add_bank_account', 'hidden', 0);
            frm.set_df_property('custom_bank_account_table', 'read_only', 1);
        }
        frm.fields_dict["custom_bank_account_table"].$wrapper
        .find(".grid-body .rows")
        .find(".grid-row")
        .each(function (i, item) {
            let field = $(item).find('[data-fieldname="change_status"]');
            field.empty();
    
            let container = $('<div class="reconcile-btn-container"></div>').css({
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                height: "100%",
            });
    
            let button = $("<button class='btn btn-xs btn-success'>Change Status</button>").css({});
    
            container.append(button);
            field.append(container);
    
            // Handle button click event
            button.click(function (event) {
                event.preventDefault();  
                // Get the `cdt` and `cdn` for the row
                let cdt = frm.fields_dict["custom_bank_account_table"].grid.doctype;
                let cdn = $(item).attr("data-name");
                const row = locals[cdt][cdn];
                
                if(row.account_name !== undefined && row.bank !== undefined){
                    name_doc = String(row.account_name+' - '+row.bank)
                }else{
                    name_doc=''
                }
                console.log('row:',name_doc);
                // if (frm.doc.workflow_state === 'Approved' && name_doc.length > 0) {
                if (name_doc.length > 0) {
                    const url = `/app/bank-account/${name_doc}`;
                    window.open(url, '_blank'); // Open the URL in a new tab
                } else {
                    frappe.msgprint(__('No linked Bank Account found for this row.'));
                }
                
            });
        });

        // if(frm.doc.custom_bank_account_table.length === 0 && frm.doc.workflow_state === 'Approved'){
        //     frm.set_df_property('custom_bank_account_table', 'read_only', 1);
        //     frm.set_df_property('custom_add_bank_account', 'hidden', 0);
        //     if(frm.doc.workflow_state === 'Approved'){
        //         frappe.call({
        //             method: "mantra_dev.backend_code.api.fetch_existing_documents",
        //             args: {
        //                 doc: frm.doc.custom_bank_account_table,
        //                 name: frm.doc.name,
        //             },
        //             callback: function (r) {
        //                 // console.log('refresh: ',r);
        //                 frm.refresh_field('custom_bank_account_table')     
        //             }
        //         })  
        //     }
        // }else{
            if (frm.doc.custom_update_data === 1){
                    frappe.call({
                        method: "mantra_dev.backend_code.api.fetch_existing_documents",
                        args: {
                            doc: frm.doc.custom_bank_account_table,
                            name: frm.doc.name,
                        },
                        callback: function (r) {
                            frm.refresh_field('custom_bank_account_table')     
                        }
                    })  
                }
        // }
    },
    after_workflow_action: function(frm) {
            console.log('Parth',frm.doc.custom_bank_account_table);
            frappe.call({
				method: "mantra_dev.backend_code.api.create_bank_account",
				args: {
                    doc: frm.doc.custom_bank_account_table,
                    name: frm.doc.name
				},
				callback: function (r) {
					console.log(r.message);
				}
			})
            
        },
        
    after_save(frm){
            frappe.call({
                method: "mantra_dev.backend_code.api.create_bank_account",
                args: {
                    doc: frm.doc.custom_bank_account_table,
                    name: frm.doc.name
                },
                callback: function (r) {
                    console.log(r.message);
                    frappe.call({
                        method: "mantra_dev.backend_code.api.fetch_existing_documents",
                        args: {
                            doc: frm.doc.custom_bank_account_table,
                            name: frm.doc.name,
                        },
                        callback: function (r) {
                            // console.log('refresh: ',r);
                            frm.refresh_field('custom_bank_account_table')
                            frm.reload_doc()   
                        }
                    })  
                }
            })

        },

        before_workflow_action(frm){
            frappe.dom.unfreeze();
            if(frm.doc.custom_bank_account_table.length === 0 ){
                if(!frappe.user_roles.includes("System Manager") && frm.doc.workflow_state === 'Reviewed'){
                    frappe.throw("There is no Bank Account for this Supplier")
                }   
            }
        },

        custom_add_bank_account(frm){
            account_table = frm.doc.custom_bank_account_table
            name1 = frm.doc.name
            frm = frm
            showBankAccountDialog(account_table, name1, frm)
        }

})

frappe.ui.form.on('Bank Account Table', {


    change_status: function (frm, cdt, cdn) {
        // Get the current row's data
        const row = locals[cdt][cdn];
        if(row.account_name !== undefined && row.bank !== undefined){
            name_doc = String(row.account_name+' - '+row.bank)
        }else{
            name_doc=''
        }
            console.log('row:',name_doc);
        
        // Ensure the row has a linked document (e.g., linked_bank_account)
        // if (frm.doc.workflow_state === 'Approved' && name_doc.length > 0) {
        if (name_doc.length > 0) {
            // Redirect to the Bank Account List View with a filter applied
            const url = `/app/bank-account/${name_doc}`;
            // const url = `/app/bank-account?filters=[["name","=","${name_doc}"]]`;
            window.open(url, '_blank'); // Open the URL in a new tab
        } else {
            frappe.msgprint(__('No linked Bank Account found for this row.'));
        }
    }
});

function showBankAccountDialog(account_table, name1, frm) {
    let d = new frappe.ui.Dialog({
      title: "Add New Bank Account",
      fields: [
        {
          label: "Bank",
          fieldname: "bank",
          fieldtype: "Link",
          options: "Bank",
          reqd: 1,
        },
        {
          label: "Bank Account Number",
          fieldname: "bank_account_no",
          fieldtype: "Data",
          reqd: 1,
        },
        {
          label: "Bank Account Name",
          fieldname: "account_name",
          fieldtype: "Data",
          reqd: 1,
        },
        {
          label: "IFSC",
          fieldname: "ifsc",
          fieldtype: "Data",
          reqd: 0,
        },
        {
          label: "Branch Location",
          fieldname: "branch_location",
          fieldtype: "Data",
          reqd: 0,
        },
        {
          label: "Branch Code",
          fieldname: "branch_code",
          fieldtype: "Data",
          reqd: 0,
        },
      ],
      size: "small",
      primary_action_label: "Submit",
      primary_action: function (doc) {
        d.hide();
        frappe.call({
            method: "mantra_dev.backend_code.api.add_bank_account",
            args: {
                doc: doc,
                name1: name1,
                account_table: account_table
            },
            callback: function (r) {
                console.log(r.message);
                frm.reload_doc();     
            }
        })
      },
    });
  
    d.show();
  }