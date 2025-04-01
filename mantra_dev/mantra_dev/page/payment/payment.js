frappe.pages['payment'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Payment Page',
        single_column: true
    });

    this.lastSelectedPayrollEntry = '';
    this.lastSelectedBankAccount='';
    let filterContainer = $('<div class="filter-container" style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; justify-content: space-between;"></div>').appendTo(page.body);

    let transaction_summary_table = $(`<table id="transaction-summary-table" style="margin-bottom: 20px; width: 100%; border-collapse: collapse; font-family: var(--font-stack);">
        <thead>
            <tr>
                <th style="background-color: var(--subtle-fg); color: var(--text-color) !important; padding:10px; text-align: center;">Total Transactions</th>
                <th style="background-color: var(--subtle-fg); color: var(--text-color) !important; padding:10px; text-align: center;">Total Amount (₹)</th>
                <th style="background-color: var(--subtle-fg); color: var(--text-color) !important; padding:10px; text-align: center;">Selected Transactions</th>
                <th style="background-color: var(--subtle-fg); color: var(--text-color) !important; padding:10px; text-align: center;">Total Selected Transcation Amount (₹)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="text-align:center; padding:10px;font-size:16px;"><span id="total-transactions">0</span></td>
                <td style="text-align:center; padding:10px;font-size:16px;"><span id="total-amount">${(format_currency(0, 'INR', precision = 2))}</span></td>
                <td style="text-align:center; padding:10px;font-size:16px;"><span id="selected-count">0</span></td>
                <td style="text-align:center; padding:10px;font-size:16px;"><span id="selected-amount">${(format_currency(0, 'INR', precision = 2))}</span></td>
            </tr>
        </tbody>
    </table>`).appendTo(page.body);


    var tableContainer = $(`<div id="group-table-container" style="max-height:500px; overflow-y:auto; scrollbar-width: none;">
  </div>`).appendTo(page.body);

    this.form = new frappe.ui.FieldGroup({
        fields: [
			{
				label: __("Use Payroll Entry"),
				fieldname: "use_payroll_entry",
				fieldtype: "Check",
				class:'use-payroll-id',
				default: 0,
				change: () => {
                    $(tableContainer).hide();
                    let usePayroll = this.form.get_value("use_payroll_entry");
                    let isPayrollEnabled = usePayroll == 1;
                
                    // Toggle visibility of fields
                    this.form.set_df_property("bank", "hidden", isPayrollEnabled);
                    this.form.set_df_property("bank_account", "hidden", isPayrollEnabled);
                    this.form.set_df_property("payroll_entry", "hidden", !isPayrollEnabled);
                
                    // Reset values
                    this.form.set_value("bank", "");
                    this.form.set_value("bank_account", "");
                    this.form.set_value("payroll_entry", isPayrollEnabled ? "" : null);
                
                    // Reset transaction summary
                    resetSummary()
                }
			},
            {
                fieldtype: "Column Break"
            },
            {
                label: __("Bank"),
                fieldname: "bank",
                fieldtype: "Link",
                options: "Bank",
                reqd: 1,
                change: () => {
                    let selectedBank = this.form.get_value("bank");
                    bank = selectedBank;
                
                    if (!selectedBank) {
                        this.form.set_value("bank_account", "");
                        $(tableContainer).hide();
                
                        resetSummary()
                    } else if (this.form.get_value("bank_account")) {
                        this.form.set_value("bank_account", "");
                    }
                }
            },
			{
				label: __("Payroll Entry"),
				fieldname: "payroll_entry",
				fieldtype: "Link",
				options: "Payroll Entry",
				hidden: true,  // Initially hidden
				reqd: 1,
				depends_on: "use_payroll_entry",
				get_query: () => {
					return {
						filters: {
							status: "Submitted",
							custom_salary_slip_file_generated:0,
                            custom_payroll_entry_approved:1
						}
					};
				},
                change: () => {
                    let selectedPayrollEntry = this.form.get_value("payroll_entry");
                    if (this.lastSelectedPayrollEntry !== selectedPayrollEntry) {
                        this.lastSelectedPayrollEntry = selectedPayrollEntry; // Store last selected value
        
                        if (selectedPayrollEntry) {
                            this.fetchPayrollEntries(selectedPayrollEntry);
                        } else {
                            $(tableContainer).empty();
                            resetSummary();
                        }
                    }
                }
			},
            {
                fieldtype: "Column Break"
            },
            {
                label: __("Bank Account"),
                fieldname: "bank_account",
                fieldtype: "Link",
                options: "Bank Integration",
                reqd: 1,
                depends_on: "bank",
                get_query: () => {
                    let selectedBank = this.form.get_value("bank");
                    if (!selectedBank) {
                        return { filters: { name: ["=", ""] } };
                    }
                    return {
                        filters: {
                            bank: selectedBank,
                            payments: 1,
                            enabled: 1
                        }
                    };
                },
                change: () => {
                    let selectedBank = this.form.get_value("bank");
                    let selectedBankAccount = this.form.get_value("bank_account");
                
                    // Prevent duplicate calls
                    if (this.lastSelectedBankAccount === selectedBankAccount) {
                        return; // Do nothing if the value hasn't changed
                    }
                    this.lastSelectedBankAccount = selectedBankAccount; // Store the last selected value
                
                    if (selectedBankAccount && !selectedBank) {
                        frappe.msgprint(__('Please select a bank before selecting a bank account.'));
                        this.form.set_value("bank_account", "");
                        return;
                    }
                
                    if (selectedBankAccount) {
                        $("#export-to-excel").show();
                        this.fetchPaymentEntries(selectedBankAccount);
                    } else {
                        $(tableContainer).hide();
                        $("#export-to-excel").hide();
                        resetSummary();
                    }
                }
            },
        ],
        body: filterContainer
    });
    this.form.make();
    document.addEventListener("change", function (event) {
        const target = event.target;
    
        if (target.classList.contains("select-all")) {
            event.stopPropagation();
            frappe.dom.freeze(); // Show freeze UI
    
            setTimeout(() => {
                const isChecked = target.checked;
                document.querySelectorAll(".group-checkbox, .entry-checkbox").forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
    
                updateTransactionSummary();
                frappe.dom.unfreeze(); // Unfreeze UI
            }, 0);
        } 
        else if (target.classList.contains("entry-checkbox")) {
            frappe.dom.freeze(); 
            setTimeout(() => {
            const partyId = target.dataset.party;
            const partyCheckboxes = document.querySelectorAll(`.party-${partyId} .entry-checkbox`);
            const allChecked = [...partyCheckboxes].every(checkbox => checkbox.checked);
    
            const groupCheckbox = document.querySelector(`.group-checkbox[data-party="${partyId}"]`);
            if (groupCheckbox) groupCheckbox.checked = allChecked;
    
            updateTransactionSummary();
            frappe.dom.unfreeze(); 
        },0);
        }
        else if (target.classList.contains("group-checkbox")) {
            frappe.dom.freeze(); 
    
            setTimeout(() => {
                const partyId = target.dataset.party;
                const isChecked = target.checked;
    
                document.querySelectorAll(`.party-${partyId} .entry-checkbox`).forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
    
                updateTransactionSummary();
                frappe.dom.unfreeze(); // Unfreeze UI
            }, 0);
        }
    });
    
    

    $("input").css({ "width": "auto" });
	$(".frappe-control[data-fieldname='use_payroll_entry']").css({
		"margin-top": "18px",
		"padding": "10px",
		"border-radius": "5px"
	});
	
    $(".form-layout").css({ "width": "720px" });
    
    this.fetchPaymentEntries = function (selectedBank) {
        frappe.dom.freeze(__("Fetching Payment Entries..."));
        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment.payment.select_payment_entry",
            args: {
                bank_account: selectedBank
            },
            callback: function (response) {
                let data = response.message;
                if (!data || data.length === 0) {
                    frappe.dom.unfreeze()
                    $(tableContainer).empty()
                    $(tableContainer).show()
                    $(tableContainer).html('<p style="text-align: center; font-size: 16px; color: red;">No Payment Entry Found</p>');
                    $("#total-transactions").text(0);
                    $("#total-amount").text(format_currency(0, 'INR', precision = 2));
                    $("#export-to-excel").attr("hidden", true);
                    return;
                }
                let groupedData = {};
                data.forEach(row => {
                    let groupKey = row.party || row.party_name;
                    if (!groupedData[groupKey]) {
                        groupedData[groupKey] = {
                            entries: [],
                            total_amount: 0
                        };
                    }
                    groupedData[groupKey].entries.push(row);
                    groupedData[groupKey].total_amount += parseFloat(row.base_paid_amount_after_tax);
                });
                let table_html = `
                <head>
                <style>
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 10px; text-align: center; vertical-align: middle;font-size:15px; }
                    thead { background-color: var(--subtle-fg); color: var(--text-color) !important; }
                    .toggle-arrow { cursor: pointer; font-size: 18px; }
                    .hidden-row { display: none; }
                    .indent { text-align: left;}
			

                    #transaction-summary-table tbody tr:hover, .no-hover-effect tbody tr:hover {
                        background-color: transparent !important;
                    }
                </style>
                  <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.17.3/xlsx.full.min.js"></script>
                </head>
                <table class="no-hover-effect">
                      <thead style="position: sticky; top: 0; z-index: 2;">
                        <tr>
                            <th style="text-align:left;"></th>
                            <th style="text-align:left;"><input type="checkbox" class="select-all"></th>
                            <th style="text-align:left;">ID</th>              
                            <th style="text-align:left;">Party</th>
                            <th style="text-align:left;">Detail</th>
                            <th style="text-align:left;">Total Paid Amount</th>
                            <th style="text-align:left;">Action</th>
                            <th style="text-align:left;">Details</th>
                        </tr>
                    </thead>
                    <tbody>`;
                // Initialize total variables before the loop
                let totalTransactions = 0;
                let totalAmt = 0;
				Object.keys(groupedData).forEach(groupKey => {
					let group = groupedData[groupKey];
					let payments = group.entries;
					let totalAmount = group.total_amount;
					let count = payments.length;
					let first = payments[0]; // Use the first row for summary
					let hasMultiplePayments = count > 1;
                    totalTransactions += count;
                    totalAmt += totalAmount;
				    if (payments.length === 1) {
                        let row = payments[0];
                        table_html += `<tr class="group-row">
						<td style="text-align:left">
						</td>
						<td style="text-align:left;">
							<input type="checkbox" class="entry-checkbox" data-id="${row.name}" data-party="${groupKey}">
						</td>
						<td style="text-align:left;">${hasMultiplePayments ? "" : `<a onclick="window.open('/app/payment-entry/${row.name}', '_blank')">${first.name}</a>`}</td>        
						<td style="text-align:left;">${row.party_name}</td>
						<td style="text-align:left;">
                            ${row.remarks 
                                    ? row.remarks.trim().replace(/(?:\r\n|\r|\n)/g, "<br>") + 
                                    (row.approver_names ? "<br>Approvers: " + row.approver_names : '') 
                                    : ""}
                        </td>

						<td class="group-paid-amount" style="text-align:left;">${format_currency(totalAmount, 'INR', precision = 2)}</td>
						<td style="text-align:left;">
							<button
								class="cancel-btn group-cancel btn btn-secondary" data-id="${row.name}">
								Reject
							</button>
						</td>
						<td style="text-align:left;">
							${hasMultiplePayments ? '' : `
							<button class="get-details btn btn-primary">
								Details
							</button>`}
						</td>
					</tr>`;
                    }
                    else{
                        let first = payments[0];
                        table_html +=`<tr class="group-row summary-row" data-party="${groupKey}">
						<td style="text-align:left;">
							
							  <span class="toggle-arrow" data-party="${groupKey}">
								<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevron-right">
								  <polyline points="9 18 15 12 9 6"></polyline>
								</svg>
							  </span>
						</td>
						<td style="text-align:left;">
							<input type="checkbox" class="group-checkbox" data-party="${groupKey}">
						</td>
						<td style="text-align:left;"></td>        
						<td style="text-align:left;">${first.party_name}</td>
						<td style="text-align:left;">
                           
                        </td>

						<td class="group-paid-amount" style="text-align:left;">${format_currency(totalAmount, 'INR', precision = 2)}</td>
						<td style="text-align:left;">
							<button
								class="cancel-btn group-cancel btn btn-secondary" data-id="${first.name}">
								Reject
							</button>
						</td>
						
					</tr>`;
                        payments.forEach(row => {
							table_html += `<tr class="hidden-row party-${groupKey}" style="display: none;">
								<td></td>
								<td class="indent">
									<input type="checkbox" class="entry-checkbox" data-id="${row.name}" data-party="${groupKey}">
								</td>
								<td style="text-align:left;"><a onclick="window.open('/app/payment-entry/${row.name}', '_blank')">${row.name}</a></td>  
								<td style="text-align:left;">${row.party_name}</td>
								<td style="text-align:left;">
									${row.remarks ? row.remarks.trim().replace(/(?:\r\n|\r|\n)/g, "<br>") : ""}
									${row.approver_names ? "<br>" + "Approvers: " + (row.approver_names || '-') : ''}
								</td>
								<td style="text-align:left;">${format_currency(row.base_paid_amount_after_tax, 'INR', precision = 2)}</td>
								<td style="text-align:left;">
									<button class="cancel-btn btn btn-secondary" data-id="${row.name}">
										Reject
									</button>
								</td>
								<td style="text-align:left;">
									<button class="get-details btn btn-primary">
										Details
									</button>
								</td>
							</tr>`;
						});
                    }
				
					
				});
                $("#total-transactions").text(totalTransactions);
                $("#total-amount").text(format_currency(totalAmt.toFixed(2), 'INR', precision = 2));
                table_html += `</tbody></table>`;
                $(tableContainer).html(table_html);
                frappe.dom.unfreeze()
                $(".toggle-arrow").on("click", function () {
                    let partyId = $(this).data("party");
                    let hiddenRows = $(`.party-${partyId}`);
                    if (hiddenRows.is(":visible")) {
                        hiddenRows.hide();
                        $(this).html(`<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevron-right"><polyline points="9 18 15 12 9 6"></polyline></svg>`);
                    } else {
                        hiddenRows.show();
                        $(this).html(`<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevron-down"><polyline points="6 9 12 15 18 9"></polyline></svg>`);
                    }
                });
                $(document).off("click", ".cancel-btn").on("click", ".cancel-btn", function () {

                    if($('.frappe-control[data-fieldname="use_payroll_entry"] input[type="checkbox"]').prop('checked') == true){
                        alert('You can not reject this entry');
                        return;
                    }
                    else{


                    let $btn = $(this);
                    let $row = $btn.closest("tr");
                    let paymentEntryId = $btn.data("id");
                    let partyId = $row.closest(".group-row").data("party");
                    if ($btn.hasClass("group-cancel")) {
                        let allIds = [];
                        $(`.party-${partyId} .entry-checkbox`).each(function () {
                            let childId = $(this).data("id");
                            if (childId && !allIds.includes(childId)) {
                                allIds.push(childId);
                            }
                        });
                        if (paymentEntryId && !allIds.includes(paymentEntryId)) {
                            allIds.push(paymentEntryId);
                        }
                        cancelPaymentEntry(allIds, function (success) {
                            if (success) {
                                $row.remove();
                                $(`.party-${partyId}`).remove();
                                updateTransactionSummary();
                            }
                        });
                    }
                    else {
                        partyId = $row.find(".entry-checkbox").data("party");
                        cancelPaymentEntry([paymentEntryId], function (success) {
                            if (success) {
                                $row.remove();
                                if ($(`.party-${partyId} .entry-checkbox`).length === 0) {
                                    $(`.group-row[data-party="${partyId}"]`).remove();
                                }
                                else {
                                    updateGroupPaidAmount(partyId);
                                }
                                updateTransactionSummary();
                            }
                        });

                    }
                }
                });
                if (data.length !== 0) {
                    $(tableContainer).show();
                }
                else {
                    $("#export-to-excel").attr("hidden", true);
                }

            }
        });
    };
    this.fetchPayrollEntries = function (selectedPayrollEntry) {
        frappe.dom.freeze(__("Fetching Salary Slips...")); 
        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment.payment.get_salary_slip",
            args: { payroll_entry: selectedPayrollEntry },
            callback: function (response) {
                let data = response.message || [];
                let totalTransactions = data.length;
                let totalAmt = data.reduce((sum, row) => sum + parseFloat(row.base_paid_amount_after_tax), 0);
    
                if (totalTransactions === 0) {
                    $(tableContainer).empty()
                    $(tableContainer).html('<p style="text-align: center; font-size: 16px; color: red;">No Salary Slip Found</p>');
                    resetSummary();
                    frappe.dom.unfreeze(); // Unfreezing UI after fetching
                    return;
                }
    
                let table_html = `
                    <style>
                        table { width: 100%; border-collapse: collapse; }
                        th, td { padding: 10px; text-align: left; font-size: 15px; }
                        thead { background-color: var(--subtle-fg); color: var(--text-color) !important; position: sticky; top: 0; z-index: 2; }
                    </style>
                    <table>
                        <thead>
                            <tr>
                                <th><input type="checkbox" class="select-all" hidden></th>
                                <th>ID</th>
                                <th>Party ID</th>
                                <th>Party</th>
                                <th>Total Paid Amount</th>
                            </tr>
                        </thead>
                        <tbody>`;
    
                data.forEach(row => {
                    table_html += `
                        <tr class="group-row" data-party="${row.party_name}">
                            <td><input type="checkbox" class="entry-checkbox" data-id="${row.name}" data-party="${row.party_name}" hidden></td>
                           <td><a onclick="window.open('/app/salary-slip/${row.name}', '_blank')">${row.name}</a></td>
                            <td>${row.party}</td>
                            <td>${row.party_name}</td>
                            <td>${format_currency(row.base_paid_amount_after_tax, 'INR', 2)}</td>
                        </tr>`;
                });
    
                table_html += `</tbody></table>`;
    
                $(tableContainer).html(table_html).show();
                $("#total-transactions").text(totalTransactions);
                $("#total-amount").text(format_currency(totalAmt.toFixed(2), 'INR', 2));
    
                frappe.dom.unfreeze(); // Unfreezing UI after data load
    
                setTimeout(() => {
                    $(".select-all, .entry-checkbox, .group-checkbox")
                        .prop("checked", true)
                        .trigger("change")
                        .prop("disabled", true);
                    updateTransactionSummary();
                }, 100);
            }
        });
    };
    
    // Function to reset summary when no data is found
    function resetSummary() {
        $("#total-transactions").text(0);
        $("#total-amount").text(format_currency(0, 'INR', 2));
        $("#selected-count").text(0);
        $("#selected-amount").text(format_currency(0, 'INR', 2));
    }

    $(document).on('click', '.get-details', function () {
        let paymentEntryId = $(this).closest('tr').find('td a').text().trim();
    
        if (!paymentEntryId) {
            frappe.msgprint(__('Payment Entry ID not found.'));
            return;
        }
    
        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment.payment.get_payment_entry_reference_details",
            args: { payment_entry: paymentEntryId },
            callback: function (r) {
                if (r.message) {
                    if (r.message.error) {
                        frappe.msgprint(r.message.error);
                        return;
                    }
    
                    let referenceDetails = r.message.reference_details || [];
                    let customDetails = r.message.custom_details || {};
    
                    let referenceTableRows = referenceDetails.map(item => {
                        let attachmentColumn = item["doctype"] === "Purchase Order" ? "":item["Attachments"];
    
                       
                        if (item["doctype"] === "Purchase Order" && item["Po Approval"] ) {
                            attachmentColumn += ` <button class="btn btn-primary btn-sm po-details-btn" data-po="${item["Po Approval"]}">
                                PO Details
                            </button>`;
                        }

                        let linkContent = "";
                        if (item["doctype"] === "Purchase Order") {
                            linkContent = `<b>${item["Document ID"]} - <a href="/app/purchase-order/${item['Document']}" target="_blank">${item['Document']}</a></b><br>`;
                        } else if (item["doctype"] === "Material Request") {
                            linkContent = `<b>${item["Document ID"]} - <a href="/app/material-request/${item['Document']}" target="_blank">${item['Document']}</a></b><br>`;
                        } else if (item["doctype"] === "Purchase Invoice") {
                            linkContent = `<b>${item["Document ID"]} - <a href="/app/purchase-invoice/${item['Document']}" target="_blank">${item['Document']}</a></b><br>`;
                        }
                        else if (item["doctype"] === "Purchase Receipt") {
                            linkContent = `<b>${item["Document ID"]} - <a href="/app/purchase-receipt/${item['Document']}" target="_blank">${item['Document']}</a></b><br>`;
                        }
                        else if (item["doctype"] === "Employee Advance") {
                            linkContent = `<b>${item["Document ID"]} - <a href="/app/employee-advance/${item['Document']}" target="_blank">${item['Document']}</a></b><br>`;
                        }
                        else if (item["doctype"] === "Expense Claim") {
                            linkContent = `<b>${item["Document ID"]} - <a href="/app/expense-claim/${item['Document']}" target="_blank">${item['Document']}</a></b><br>`;
                        }
    
                        return `
                            <tr>
                                <td style="text-align:left;">
                                    ${linkContent}

                                    <small>Created on: ${item["Created On"]}</small><br>
                                    <small>Submitted on: ${item["Submitted On"]}</small>
                                </td>
                                <td style="text-align:left;">${item["Purpose"] || ""}</td>
                                <td style="text-align:left;">${(item["Approvers"] || "No Approvers").split(",").join("<br>")}</td>
                                 <td style="text-align:left;">
                                 ${item['doctype'] !== 'Purchase Order' ? (
                                    item['Attachments'] && item['doctype'] !== 'Purchase Order' ? 
                                      item['Attachments'].split(',').map(attachment => 
                                        `<a href="${attachment}" target="_blank">${attachment}</a><br>`).join('') 
                                      : ''
                                  ) : ''}
                                    ${attachmentColumn}
                        </td>
                            </tr>
                        `;
                    }).join("");
    
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
                                    <td style="text-align:left;">${customDetails.custom_type || ""}</td>
                                    <td style="text-align:left;">${customDetails.custom_project_type || ""}</td>
                                    <td style="text-align:left;">${customDetails.custom_approved_by || ""}</td>
                                    <td style="text-align:left;">${customDetails.remarks || ""}</td>
                                </tr>
                            </tbody>
                        </table>
                    `;
    
                    let d = new frappe.ui.Dialog({
                        title: __("Approval Details"),
                        size: "extra-large",
                        fields: [{
                            fieldtype: "HTML",
                            options: `
                                <style>
                                    .reference-data {
                                        border-collapse: collapse;
                                        width: 100%;
                                        font-size: 14px;
                                    }
                                    .reference-data th, .reference-data td {
                                        padding: 10px;
                                        border: 1px solid #ddd;
                                        text-align: left;
                                    }
                                    .reference-data thead {
                                        font-weight: bold;    
                                    }
                                    .section-title {
                                        font-weight: bold;
                                        font-size: 16px;
                                        margin-top: 10px;
                                        margin-bottom: 5px;
                                    }
                                    .custom-details-table td{
                                        padding: 10px;
                                        border: 1px solid #ddd;
                                        text-align: left;
                                    }
                                    .custom-details-table th{
                                        padding: 10px;
                                        border: 1px solid #ddd;
                                        text-align: left;
                                    }
                                    
                                </style>
                                
                                <table class="reference-data">
                                    <thead>
                                        <tr>
                                            <th>Document</th>
                                            <th>Purpose</th>
                                            <th>Approvals</th>
                                            <th>Attachments</th>
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
    });

    $(document).on("click", ".po-details-btn", function () {
        let poId = $(this).data("po");
        if (poId) {
            frappe.open_in_new_tab = true;
            frappe.set_route("Form", "PO Form Approval", poId);
        }
        else{
           frappe.msgprint('Po Form Approval is not Found')
        }
    });
    
    
    let buttonContainer = $("<div style='display: flex; justify-content: flex-start;'>")
        .appendTo(filterContainer);

    let download_excel_btn = $(`<button id='export-to-excel' style="margin-right:10px;margin-top:10px;" class="btn btn-primary" hidden>Send Excel File </button>`)
        .appendTo(buttonContainer);

    //Comment for live
    // if (['hiren@mefron.com', 'bhavyen@mefron.com'].includes(frappe.session.user)) {



    if (['hiren@mantratec.com', 'bhavyen@mantratec.com'].includes(frappe.session.user)) {
        let make_payment_btn = $(`<button style="margin-top:10px;" class="btn btn-primary">Make Payment</button>`)
            .appendTo(buttonContainer);

        make_payment_btn.on('click', function () {
            let selected_entries = getSelectedEntries();
            if($('.frappe-control[data-fieldname="use_payroll_entry"] input[type="checkbox"]').prop('checked') == true){

                sendOTP($('.frappe-control[data-fieldname="payroll_entry"] input').val());
            } 
            else{

            if (selected_entries.length === 0) {
                frappe.msgprint("Please select at least one payment entry");
            } else {
                showBankAccountDialog();
            }
        }
        });
    }

    $(document).on('click', '#export-to-excel', function () {
        // Create a new Frappe Dialog for selecting a user email
        let d = new frappe.ui.Dialog({
            title: 'Select User to Send Email',
            fields: [
                {
                    label: 'User Email',
                    fieldname: 'user_email',
                    fieldtype: 'Link',
                    options: 'User'
                }
            ],
            primary_action_label: 'Submit',
            primary_action(values) {
                let selectedUser = values.user_email;
                generateExcelAndSend(selectedUser);
                d.hide();
            }
        });
        d.show();
    });

}

function generateExcelAndSend(selectedUser) {

    $('.hidden-row').css('display', 'table-row');
    let tableClone = $('.no-hover-effect').clone();
    tableClone.find('th:first-child, td:first-child').remove();
    tableClone.find('th:nth-child(1), td:nth-child(1)').remove();
    tableClone.find('th:nth-child(5), td:nth-child(5)').remove();
    tableClone.find('th:last-child, td:last-child').remove();

    let rows = tableClone.find('tr');
    let wb = XLSX.utils.book_new();
    let ws_data = [];

    let lastParty = null;
    let partyTotal = 0;
    let outputRows = [];

    rows.each(function (index, row) {
        let rowData = [];
        let paidAmountText = $(row).find('td').last().text().trim();
        let paidAmount = parseFloat(paidAmountText.replace(/[^0-9.-]+/g, "")) || 0;
        $(row).find('td, th').each(function () {
            rowData.push($(this).text().trim());
        });
        let currentParty = rowData[1];
        if (lastParty !== null && currentParty !== lastParty) {

            if (partyTotal !== 0) {
                outputRows.push(["", "", "", "","" + format_currency(partyTotal.toFixed(2), 'INR', precision = 2)]);
            }
            partyTotal = 0;
        }
        if (rowData[0] !== "") {
            outputRows.push(rowData);
            partyTotal += paidAmount;
        }
        lastParty = currentParty;
    });
    if (lastParty !== null) {
        outputRows.push(["", "", "","","" + format_currency(partyTotal.toFixed(2), 'INR', precision = 2)]);
    }
    ws_data = ws_data.concat(outputRows);

    let ws = XLSX.utils.aoa_to_sheet(ws_data);
    ws['!cols'] = [
        { wch: 20 },  // width for ID column
        { wch: 30 },  // width for Party column
        { wch: 100 },  // width for Reference No column
        { wch: 20 }   // width for Total Paid Amount column
    ];
    XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
    let workbookOutput = XLSX.write(wb, { bookType: 'xlsx', type: 'binary' });
    $('.hidden-row').css('display', 'none');
    let base64File = btoa(workbookOutput);

    // Use frappe.call to send the email with the Excel file attachment
    frappe.call({
        method: "mantra_dev.mantra_dev.page.payment.payment.send_excel_email",  // Update with your app's path
        args: {
            user_email: selectedUser,
            filename: "payment_data.xlsx",
            filedata: base64File,
            subject: "Payment Entry Details"
        },
        callback: function (response) {
            if (response.message === "Email Sent") {
                frappe.msgprint("Email sent successfully to " + selectedUser);
            } else {
                frappe.msgprint("There was an error sending the email.");
            }
        }
    });

}
function updateGroupPaidAmount(partyId) {
    let totalPaidAmount = 0;
    $(`.party-${partyId} .entry-checkbox`).each(function () {
        let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
        // Remove the currency symbol, commas, and any extra spaces
        let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());
        if (!isNaN(amount)) {
            totalPaidAmount += amount;
        }
    });
    let groupRow = $(`.group-row[data-party="${partyId}"]`);
    groupRow.find(".group-paid-amount").text(format_currency(totalPaidAmount.toFixed(2), 'INR', precision = 2));
}

function cancelPaymentEntry(paymentEntryIds, callback) {
    frappe.call({
        method: "mantra_dev.mantra_dev.page.payment.payment.cancel_payment_entries",
        args: {
            payment_entry_ids: paymentEntryIds
        },
        callback: function (response) {
            if (response.message === "Success") {
                updateTransactionSummary()
                callback(true); // Call the callback function with success = true
            } else {
                frappe.msgprint(__('Failed to cancel payment entries.'));
                callback(false); // Call the callback function with success = false
            }
        }
    });
}
function showBankAccountDialog() {
    let d = new frappe.ui.Dialog({
        title: "Select Bank Account",
        fields: [
            {
                label: "Bank",
                fieldname: "bank",
                fieldtype: "Link",
                options: "Bank",
                reqd: 1,
                default: $('.frappe-control[data-fieldname="bank"] input').val()

            },
            {
                label: "Bank Account",
                fieldname: "bank_account",
                fieldtype: "Link",
                options: "Bank Integration",
                reqd: 1,
                default: $('.frappe-control[data-fieldname="bank_account"] input').val(),

                get_query: () => {
                    return {
                        filters: [
                            ["bank", "=", d.get_value("bank")],
                            ["payments", "=", 1],
                            ["enabled", "=", 1],
                        ],
                    };
                },
            },
        ],
        size: "small",
        primary_action_label: "Submit",
        primary_action: function (values) {
            d.hide();
            sendOTP(values.bank_account);
        },
    });
    d.show();
}

function sendOTP(bank_account) {
    frappe.dom.freeze("Please wait... Sending OTP");
    frappe.call({
        method: "mantra_dev.api_code.bank_transaction.send_otp",
        args: {
            email: frappe.session.user,
        },
        callback: function (r) {
            if (r.message) {
                frappe.dom.unfreeze();
                showOTPDIalog(bank_account);
            }
        },
    });
}

function showOTPDIalog(bank_account) {
    let d1 = new frappe.ui.Dialog({
        title: "Enter OTP",
        fields: [
            {
                label: "OTP",
                fieldname: "otp",
                fieldtype: "Data",
                reqd: 1,
            },
        ],
        size: "small",
        primary_action_label: "Submit",
        primary_action: function (values) {
            d1.hide();
            verifyotp(values.otp, bank_account);
        },
    });
    d1.show();
}
function verifyotp(otp, bank_account) {

    frappe.call({
        method: "mantra_dev.api_code.bank_transaction.verify_otp",
        args: {
            email: frappe.session.user,
            otp: otp,
        },
        callback: function (r) {
            if (r.message) {
                if (r.message == "Done") {
                    let selected_entries = getSelectedEntries();
                    selectPaymentEntry(selected_entries, bank_account)
                }
                if (r.message == "Error") {
                    frappe.throw("Verifivation Code Is Incorrect, Please Ckeck & Enter")
                }
                if (r.message == "Expired") {
                    frappe.throw("Verifivation Code Is Expired, Plese Retry Process")
                }
            }
        },
    });
}

function selectPaymentEntry(data, bank_account) {

    frappe.confirm(
        "Transaction Details:".concat(
            "<br>",
            "Total transaction: ", parseInt($("#selected-count").text()) || 0, "<br>",
            "Total amount: ", format_currency(parseFloat($("#selected-amount").text().replace('₹', '').replace(/,/g, '').trim()) || 0, 'INR', precision = 2)
        ),
        function () {

            if($('.frappe-control[data-fieldname="use_payroll_entry"] input[type="checkbox"]').prop('checked') == true){
                frappe.call({
                    method: "mantra_dev.api_code.bank_transaction.generate_payroll_payment_file",
                    args: {
                        payroll_entry: bank_account,
                        create_only_file: 0,
                    },
                    callback: function (r) {
                        if (r.message) {
                            if (r.message.status_code == 200) {
                                // If success, open the external URL
                                removeSelectedRows();
                                updateTransactionSummary()
                                let selectedPartyIds = [];
                                $(".group-row").each(function () {
                                    let partyId = $(this).data("party");
                                    if (partyId && !selectedPartyIds.includes(partyId)) {
                                        selectedPartyIds.push(partyId);
                                    }
                                });
                                selectedPartyIds.forEach(function (partyId) {
                                    updateGroupPaidAmount(partyId);
                                });
                            }
                            else{
                                alert(r.message.message);
                            }
                        }
                    },
                });
            }else{
                frappe.call({
                    method: "mantra_dev.api_code.bank_transaction.upload_file",
                    args: {
                        payment_entry_list: data,
                        bank_account: bank_account,
                    },
                    callback: function (r) {
                        if (r.message) {
                            if (r.message == "Done") {
                                // If success, open the external URL
                                removeSelectedRows();
                                updateTransactionSummary()
                                let selectedPartyIds = [];
                                $(".group-row").each(function () {
                                    let partyId = $(this).data("party");
                                    if (partyId && !selectedPartyIds.includes(partyId)) {
                                        selectedPartyIds.push(partyId);
                                    }
                                });
                                selectedPartyIds.forEach(function (partyId) {
                                    updateGroupPaidAmount(partyId);
                                });
                                window.open("https://cibnext.icicibank.com/corp/AuthenticationController?FORMSGROUP_ID__=AuthenticationFG&__START_TRAN_FLAG__=Y&FG_BUTTONS__=LOAD&ACTION.LOAD=Y&AuthenticationFG.LOGIN_FLAG=1&BANK_ID=ICI&ITM=nli_corp_primer_login_btn_desk", "_blank");
                            }else{
                                frappe.msgprint(r.message)
                            }
                        }
                    },
                });
            }
        },
    )
}


function removeSelectedRows() {
    $("input[type='checkbox']:checked").closest("tr").remove();
}


function updateTransactionSummary() {
    let selectedCount = 0;
    let selectedAmount = 0;
    let totalTransactionCount = 0;
    let totalTransactionAmount = 0;

    $(".group-row").each(function () {
        let partyId = $(this).data("party");
        let groupCheckbox = $(`.group-checkbox[data-party="${partyId}"]`);
        let groupChildren = $(`.party-${partyId} .entry-checkbox`);
        let usePayrollEntryChecked = $('.frappe-control[data-fieldname="use_payroll_entry"] input[type="checkbox"]').prop('checked');

        // If the party has only one entry, it won't have child rows
        if (groupChildren.length === 0) {
            totalTransactionCount++;
            let amountColumnIndex = usePayrollEntryChecked ? 5 : 6;
            let amountText = $(this).find(`td:nth-child(${amountColumnIndex})`).text();
            let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

            if (!isNaN(amount)) {
                totalTransactionAmount += amount;
            }

            // Check if this single-row entry is selected
            if ($(this).find(".entry-checkbox").prop("checked")) {
                selectedCount++;
                selectedAmount += amount;
            }
        } else {
            let amountColumnIndex = usePayrollEntryChecked ? 5 : 6;
            // Multiple transactions under a group
            totalTransactionCount += groupChildren.length;
            groupChildren.each(function () {
                let amountText = $(this).closest("tr").find(`td:nth-child(${amountColumnIndex})`).text();
                let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

                if (!isNaN(amount)) {
                    totalTransactionAmount += amount;
                }
            });

            if (groupCheckbox.prop("checked")) {
                selectedCount += groupChildren.length;
                groupChildren.each(function () {
                    let amountText = $(this).closest("tr").find(`td:nth-child(${amountColumnIndex})`).text();
                    let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

                    if (!isNaN(amount)) {
                        selectedAmount += amount;
                    }
                });
            } else {
                // Count only selected child rows if the group is not checked
                groupChildren.filter(":checked").each(function () {
                    selectedCount++;
                    let amountText = $(this).closest("tr").find(`td:nth-child(${amountColumnIndex})`).text();
                    let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

                    if (!isNaN(amount)) {
                        selectedAmount += amount;
                    }
                });
            }
        }
    });

    // Update UI
    $("#selected-count").text(selectedCount);
    $("#selected-amount").text(format_currency(selectedAmount.toFixed(2), 'INR', precision = 2));
    $("#total-transactions").text(totalTransactionCount);
    $("#total-amount").text(format_currency(totalTransactionAmount.toFixed(2), 'INR', precision = 2));
}


function getSelectedEntries() {
    let selectedEntries = new Set();

    $(".group-row").each(function () {
        let partyId = $(this).data("party");
        let groupCheckbox = $(`.group-checkbox[data-party="${partyId}"]`);
        let groupChildren = $(`.party-${partyId} .entry-checkbox`);

        // If the party has only one entry (no child rows)
        if (groupChildren.length === 0) {
            let singleEntryCheckbox = $(this).find(".entry-checkbox");
            if (singleEntryCheckbox.prop("checked")) {
                selectedEntries.add(singleEntryCheckbox.data("id"));
            }
        } else {
            // Handle grouped entries
            if (groupCheckbox.prop("checked")) {
                groupChildren.each(function () {
                    selectedEntries.add($(this).data("id"));
                });
            } else {
                groupChildren.filter(":checked").each(function () {
                    selectedEntries.add($(this).data("id"));
                });
            }
        }
    });

    return Array.from(selectedEntries);
}
