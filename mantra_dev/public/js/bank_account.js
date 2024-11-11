frappe.ui.form.on('Bank Account', {
    after_workflow_action(frm) {
        // return
        // Upload Approved Beneficiary file on Snorkel 
        if (frm.doc.workflow_state === "Approved") {
            if (frm.doc.party_type !== "Shareholder" && !frm.doc.is_company_account) {
                // frappe.msgprint("Hello");
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

        // Upload Cancelled Beneficiary file on Snorkel
        if (frm.doc.workflow_state === "Cancelled") {
            // return
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