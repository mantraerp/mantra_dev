// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Payment Entry Details"] = {
	"filters": [

	],
	onload: function () {
		
		//Update Remarks Button Click Event 
		$(document).on("click", ".update_remarks", function () {
			var button = $(this);
			var PaymentEntry = button.data("name");
			var Remarks = button.data("remarks");
			var Narration = button.data("narration");
			var Type = button.data("type") || "0";
			var Project = button.data("project") || "0";
			
			let d = new frappe.ui.Dialog({
				title: 'Update Remarks',
				fields: [
					{
						label: 'Payment Entry',
						fieldname: 'payment_entry',
						fieldtype: 'Data',
						read_only: 1,
						default: PaymentEntry
					},
					{
						label: 'Project And Type',
						fieldtype: 'Section Break'
					},
					{
						label: 'Type',
						fieldname: 'type',
						fieldtype: 'Data',
						default: Type,
						read_only: 0
					},
					{
						fieldtype: 'Column Break'
					},
					{
						label: 'Project',
						fieldname: 'project',
						fieldtype: 'Data',
						default: Project,
						reqd: 0,
					},
					{
						fieldtype: 'Section Break'
					},
					{
						label: 'Remarks',
						fieldname: 'remarks',
						fieldtype: 'Small Text',
						reqd: 0,
						default: Remarks
					},
					{
						fieldtype: 'Section Break'
					},
					{
						label: 'Narration',
						fieldname: 'narration',
						fieldtype: 'Small Text',
						read_only:1,
						reqd: 0,
						default: Narration
					},
				],
				primary_action_label: 'Update',
				primary_action(values) {
					frappe.call({
						method: "mantra_dev.mantra_dev.report.payment_entry_details.payment_entry_details.update_remarks",
						args:{
							payment_entry: values.payment_entry,
							remarks: values.remarks,
							type: values.type,
							project: values.project
						},
						callback : function(r){
							if (r.message.status === "success") {
								frappe.msgprint(`Payment Entry <b>${values.payment_entry}</b> updated successfully!`)
								frappe.query_report.refresh();
							}else{
								frappe.msgprint("Error: " + response.message.message);
							}
						}
					});
					d.hide()
				}
			});
			d.show();
		});

		// Get Details Button Click Event 
		$(document).on("click", ".get_details", function () {
			var button = $(this);
			var paymentEntryId = button.data("name");

			if (!paymentEntryId) {
				frappe.msgprint(__('Payment Entry ID not found.'));
				return;
			}
			frappe.call({
				method: "mantra_dev.mantra_dev.page.payment_page.payment_page.get_payment_entry_reference_details",
				args: { payment_entry: paymentEntryId },
				callback: function(r) {
					if (r.message) {
						if (r.message.error) {
							frappe.msgprint(r.message.error);
							return;
						}
						let referenceDetails = r.message.reference_details || [];
						let customDetails = r.message.custom_details || {};
		
						let referenceTableRows = referenceDetails.map(item => `
							<tr>
								<td style="text-align:left;">${(item["Reference ID"] || "N/A").split(",").join("<br>")}</td>
								<td style="text-align:left;">${(item["Doctype"] || "N/A").split(",").join("<br>")}</td>
								<td style="text-align:left;">${(item["Approvers"] || "No Approvers").split(",").join("<br>")}</td>
								<td style="text-align:left;">${(item["Approver Names"] || "N/A").split(",").join("<br>")}</td>
	
							</tr>
						`).join("");
		
						let customDetailsTable = `
							
							<table class="custom-details-table">
								<thead>
									<tr>
										<th>Type</th>
										<th>Project Type</th>
										<th>Approved By</th>
										<th>Remarks</th>
									</tr>
								</thead>
								<tbody>
									<tr>
										<td style="text-align:left;">${customDetails.custom_type || "N/A"}</td>
										<td style="text-align:left;">${customDetails.custom_project_type || "N/A"}</td>
										<td style="text-align:left;">${customDetails.custom_approved_by || "N/A"}</td>
										<td style="text-align:left;">${customDetails.remarks || "N/A"}</td>
									</tr>
								</tbody>
							</table>
						`;
		
						let d = new frappe.ui.Dialog({
							title: __("Reference Details"),
							size: "extra-large",
							fields: [{
								fieldtype: "HTML",
								options: `
									<style>
										.reference-data, .custom-details-table {
											border-collapse: collapse;
											width: 100%;
											font-size: 14px;
											
										}
										.reference-data th, .reference-data td, 
										.custom-details-table th, .custom-details-table td {
											padding: 10px;
											border: 1px solid #ddd;
											text-align: center;
										}
										.custom-details-table thead{
											font-weight: #FFFFFF;;
											background-color: #007cc3;
										}
										.reference-data thead {
											font-weight: #FFFFFF;;
											background-color: #007cc3;    
										}
										.section-title {
											font-weight: bold;
											font-size: 16px;
											margin-top: 10px;
											margin-bottom: 5px;
										}
									</style>
		
									<div class="section-title"></div>
									<table class="reference-data">
										<thead>
											<tr>
												<th>Reference ID</th>
												<th>Doctype</th>
												<th>Approvers</th>
												<th>Approver Names</th>
											</tr>
										</thead>
										<tbody>
											${referenceTableRows || `<tr><td colspan="4">No Reference Details Found</td></tr>`}
										</tbody>
									</table>
		
									<div class="section-title"></div>
									${customDetailsTable}
								`
							}]
						});
						d.show();
					}
				}
			});
		})
	}
};
