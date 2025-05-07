// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

class WorkflowOverride extends frappe.ui.form.States {

	show_actions() {
		var added = false;
		var me = this;

		// if the loaded doc is dirty, don't show workflow buttons
		if (this.frm.doc.__unsaved === 1) {
			return;
		}

		function has_approval_access(transition) {
			let approval_access = false;
			const user = frappe.session.user;
			if (
				user === "Administrator" ||
				transition.allow_self_approval ||
				user !== me.frm.doc.owner
			) {
				approval_access = true;
			}
			return approval_access;
		}

		frappe.workflow.get_transitions(this.frm.doc).then((transitions) => {
			this.frm.page.clear_actions_menu();
			transitions.forEach((d) => {
				if (frappe.user_roles.includes(d.allowed) && has_approval_access(d)) {
					added = true;
					me.frm.page.add_action_item(__(d.action), function () {
						
                        frappe.confirm('Are you sure you want to proceed?',
                            () => {

								if (me.frm.doc.doctype === "Purchase Order" && d.action === "Hold") {
									let dialog = new frappe.ui.Dialog({
										title: __("Enter reason to hold"),
										fields: [
											{
												fieldname: "reason",
												fieldtype: "Data",
												label: __("Reason"),
												reqd: 1,
											},
										],
										primary_action_label: __("Submit"),
										primary_action(values) {
											// Check if reason is provided
											if (!values.reason) {
												frappe.msgprint(__("Please enter a reason."));
												return;
											}

											// Freeze the UI during the process
											frappe.dom.freeze();

											// Call to add the comment
											frappe.call({
												method: "mantra_dev.backend_code.api.add_hold_reason_comment",
												args: {
													doc_name: me.frm.doc.name,
													action: d.action,
													reason: values.reason,
												},
												callback: function (r) {
													frappe.dom.unfreeze();
													me.frm.reload_doc();
													me.frm.script_manager.trigger("before_workflow_action").then(() => {
														frappe
															.xcall("frappe.model.workflow.apply_workflow", {
																doc: me.frm.doc,
																action: d.action,
															})
															.then((doc) => {
																frappe.model.sync(doc);
																me.frm.refresh();
																me.frm.selected_workflow_action = null;
																me.frm.script_manager.trigger("after_workflow_action");
															})
															.finally(() => {
																frappe.dom.unfreeze();
															});
													});
												},
											});
											dialog.hide();
										},
									});
									dialog.show();
								}
								else if (me.frm.doc.doctype === "Job Offer" && (d.action === "Hold" || d.action == 'Reject')) {
									let dialog = new frappe.ui.Dialog({
										title: __(d.action == 'Hold' ? "Enter Reason for On Hold" : "Enter Reason for Rejected"),
										fields: [
											{
												fieldname: "reason",
												fieldtype: "Data",
												label: __("Reason"),
												reqd: 1,
											},
										],
										primary_action_label: __("Submit"),
										primary_action(values) {
											if (!values.reason) {
												frappe.msgprint(__("Please enter a reason."));
												return;
											}

											frappe.dom.freeze();
											frappe.call({
												method: "recruitment.backend_code.job_offer.job_offer.handle_workflow_action_for_job_offer",
												args: {
													doc_name: me.frm.doc.name,
													action: d.action == 'Hold' ? "on_hold" : "reject",
													reason: values.reason,
												},
												callback: function (r) {
													frappe.dom.unfreeze();
													me.frm.reload_doc();
													me.frm.script_manager.trigger("before_workflow_action").then(() => {
														frappe
															.xcall("frappe.model.workflow.apply_workflow", {
																doc: me.frm.doc,
																action: d.action,
															})
															.then((doc) => {
																frappe.model.sync(doc);
																me.frm.refresh();
																me.frm.selected_workflow_action = null;
																me.frm.script_manager.trigger("after_workflow_action");
															})
															.finally(() => {
																frappe.dom.unfreeze();
															});
													});


												},
											});

											dialog.hide();
										},
									});

									dialog.show();
								}
								else if (me.frm.doc.doctype === "Job Requisition" && d.action == 'Reject') {
									let dialog = new frappe.ui.Dialog({
										title: __("Enter Reason for Rejected"),
										fields: [
											{
												fieldname: "reason",
												fieldtype: "Data",
												label: __("Reason"),
												reqd: 1,
											},
										],
										primary_action_label: __("Submit"),
										primary_action(values) {
											if (!values.reason) {
												frappe.msgprint(__("Please enter a reason."));
												return;
											}

											frappe.dom.freeze();
											frappe.call({
												method: "recruitment.backend_code.job_requisition.job_requisition.handle_workflow_action",
												args: {
													doc_name: me.frm.doc.name,
													action: "reject",
													reason: values.reason
												},

												callback: function (r) {
													frappe.dom.unfreeze();
													me.frm.reload_doc();
													me.frm.script_manager.trigger("before_workflow_action").then(() => {
														frappe
															.xcall("frappe.model.workflow.apply_workflow", {
																doc: me.frm.doc,
																action: d.action,
															})
															.then((doc) => {
																frappe.model.sync(doc);
																me.frm.refresh();
																me.frm.selected_workflow_action = null;
																me.frm.script_manager.trigger("after_workflow_action");
															})
															.finally(() => {
																frappe.dom.unfreeze();
															});
													});


												},
											});

											dialog.hide();
										},
									});

									dialog.show();
								}
								else{
								// action to perform if Yes is selected
                                //transition start
                                // set the workflow_action for use in form scripts
                                frappe.dom.freeze();
                                me.frm.selected_workflow_action = d.action;
                                me.frm.script_manager.trigger("before_workflow_action").then(() => {
                                    frappe
                                        .xcall("frappe.model.workflow.apply_workflow", {
                                            doc: me.frm.doc,
                                            action: d.action,
                                        })
                                        .then((doc) => {
                                            frappe.model.sync(doc);
                                            me.frm.refresh();
                                            me.frm.selected_workflow_action = null;
                                            me.frm.script_manager.trigger("after_workflow_action");
                                        })
                                        .finally(() => {
                                            frappe.dom.unfreeze();
                                        });
									});
								}

                            }, () => {
                                // action to perform if No is selected
                            })
					});
				}
			});

			this.setup_btn(added);
		});
	}

};

frappe.ui.form.States = WorkflowOverride
