frappe.ui.form.on('Bank Account', {
    refresh: function (frm) {
        if(frappe.session.user==="abhishek.jain@mantratec.com"||frappe.session.user==="anurag@mantratec.com"||frappe.session.user==="Administrator")
        {
            frm.add_custom_button("Create beny with A (New)", function() {
                frappe.call({
                    method: "mantra_dev.api_code.banck_transaction.upload_beneficiary_file",
                    args: {
                        doc_name: frm.doc.name,
                    },
                    callback: function (r) {
                        if (r.message) {
                            console.log(r.message);
                            frappe.msgprint(r.message);
                        }
                    }
                });
            }, "Utility");
            frm.add_custom_button("Create beny with M (Modified)", function() {
                frappe.call({
                    method: "mantra_dev.api_code.banck_transaction.upload_beneficiary_file_for_modified_doc",
                    args: {
                        doc_name: frm.doc.name,
                    },
                    callback: function (r) {
                        if (r.message) {
                            console.log(r.message);
                            frappe.msgprint(r.message);
                        }
                    }
                });
            }, "Utility");
            frm.add_custom_button("Create beny with D (DELETE)", function() {
                frappe.call({
                    method: "mantra_dev.api_code.banck_transaction.upload_beneficiary_file_for_cancelled_doc",
                    args: {
                        doc_name: frm.doc.name,
                    },
                    callback: function (r) {
                        if (r.message) {
                            console.log(r.message);
                            frappe.msgprint(r.message);
                        }
                    }
                });
            }, "Utility");
        }
    },
    before_workflow_action(frm) {
        // Upload Approved Beneficiary file on Snorkel
        if (frm.doc.workflow_state === "Pending" && frm.selected_workflow_action === 'Approve') {
            if (frm.doc.party_type !== "Shareholder" && !frm.doc.is_company_account) {
                frappe.call({
                    method: "mantra_dev.api_code.banck_transaction.upload_beneficiary_file",
                    args: {
                        doc_name: frm.doc.name,
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint(r.message);
                        }
                    }
                });
            }
        }

        // Upload Modified Approved Beneficiary file on Snorkel
        if (frm.doc.workflow_state === "Rejected" && frm.selected_workflow_action === 'Approve') {
            if (frm.doc.party_type !== "Shareholder" && !frm.doc.is_company_account) {
                
                frappe.call({
                    method: "mantra_dev.api_code.banck_transaction.upload_beneficiary_file_for_modified_doc",
                    args: {
                        doc_name: frm.doc.name,
                    },
                    callback: function (r) {
                        if (r.message) {
                            console.log(r.message);
                            frappe.msgprint(r.message);
                        }
                    }
                });
            }
        }
    },

    after_workflow_action(frm) {
        if (frm.doc.party_type === "Supplier"){
            frappe.db.set_value('Supplier', frm.doc.party, "custom_update_data", 1)
        }
        // Upload Cancelled Beneficiary file on Snorkel
        if (frm.doc.workflow_state === "Cancelled") {
            if (frm.doc.party_type !== "Shareholder" && !frm.doc.is_company_account) {
                // frappe.msgprint("Hello");
                frappe.call({
                    method: "mantra_dev.api_code.banck_transaction.upload_beneficiary_file_for_cancelled_doc",
                    args: {
                        doc_name: frm.doc.name,
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint(r.message);
                        }
                    }
                });
            }
        }
    },
    after_save(frm){
        if (frm.doc.party_type === "Supplier"){
            frappe.db.set_value('Supplier', frm.doc.party, "custom_update_data", 1)
        }
    },
    custom_ifsc(frm){
        let value = frm.doc.custom_ifsc || "";
        if (value.length > 10) {
            console.log("Value is longer than 10 characters");
            // You can also do something like:
            // frappe.validated = false; to stop form submission
            frappe.call({
                method: "mantra.backend_code.globle.branch_name_using_ifsc",
                args: { 
                    ifsc:frm.doc.custom_ifsc,
                },
                freeze: true,
                freeze_message: "Check IFSC code wait...",
                callback: function (r) {
                    console.log(String(r.message));
                    frm.set_value('custom_branch_location', String(r.message));
                    // frm.doc.custom_branch_location = r.message
                }
            });
        }
    },
});