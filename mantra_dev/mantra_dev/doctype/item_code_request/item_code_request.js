// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.ui.form.on("Item Code Request", {
	refresh(frm) {
    },
    
    
    after_workflow_action: function(frm) {
        if (frm.doc.workflow_state === 'Approved'){
            frappe.confirm(`Are you sure you want to share this item ${frm.doc.new_item_code} to this User${frm.doc.requested_by}?`,
                () => {
                    // action to perform if Yes is selected
                    frappe.call({
                        method: "mantra_dev.backend_code.api.share_item_with_user",
                        args: {
                            item_code: frm.doc.new_item_code,
                            user_email: frm.doc.requested_by,
                        },
                        callback: function (r) {
                            frappe.msgprint(r.message)    
                        }
                    })
                }, () => {
                    // action to perform if No is selected
                })
        }
    },



});
