frappe.ui.form.on('Payment Request', {
	onload:function(frm) {
		var party_type = frm.doc.party_type;
		var party = frm.doc.party;
		
		    frappe.call({
		        method: "mantra_dev.backend_code.api.get_party_name",
		        args: {
		            "party_type": party_type,
		            "party": party,
		        }
		    }).then(r => {
		        var party_name = r.message;
		       frm.set_value('custom_party_name', party_name);
		    });
		  frm.set_query("bank_account", function () {
			return {
				filters: {
					is_company_account: 0,
					party_type: frm.doc.party_type,
					party: frm.doc.party,
					workflow_state: "Approved",
					
				},
			};
		});
	},
	refresh:function(frm){
        if(["Purchase Order","Purchase Invoice"].includes(frm.doc.reference_doctype)){
        frm.add_custom_button(("Details"), async () => {
            try {
                // Fetch document details via Frappe backend
                let response = await new Promise((resolve, reject) => {
                    frappe.call({
                        method: "mantra_dev.backend_code.detail_popup.fetch_document_details",
                        args: {
                            doctype: "Payment Request",
                            docname: frm.doc.name
                        },
                        callback: function(r) {
                            console.log(r.message)
                            if (r.message) {
                                resolve(r.message);
                            } else {
                                reject("Error fetching document details");
                            }
                        }
                    });
                });

                // Create and display dialog with the fetched HTML
                let d = new frappe.ui.Dialog({
                    title: __("Purchase Order Details"),
                    fields: [
                        {
                            fieldtype: "HTML",
                            fieldname: "po_details",
                            options: response
                        }
                    ],
                    size: response =='This document does not have an associated purchase order.' ? 'small' :'extra-large',
                    primary_action_label: __("Close"),
                    primary_action: () => d.hide()
                });

                d.show();
            } catch (error) {
                console.error(error);
                frappe.msgprint(__("Failed to fetch purchase order details"));
            }
        
        })
    }
	}
});