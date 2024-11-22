frappe.ui.form.on('Bank Account', {
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
                            console.log(r.message);
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
                            console.log(r.message);
                            frappe.msgprint(r.message);
                        }
                    }
                });
            }
        }
    },

});