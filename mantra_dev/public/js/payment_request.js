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
	}
});