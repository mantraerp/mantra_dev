frappe.pages['payment'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Payment Page',
        single_column: true
    });

    let filterContainer = $('<div class="filter-container" style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; justify-content: space-between;"></div>').appendTo(page.body);

    let transaction_summary_table = $(`<table id="transaction-summary-table" style="margin-bottom: 20px; width: 100%; border-collapse: collapse;">
        <thead>
            <tr>
                <th style="background-color: #007cc3; color:white;padding:10px; text-align: center;">Total Transactions</th>
                <th style="background-color: #007cc3; color:white;padding:10px; text-align: center;">Total Amount (₹)</th>
                <th style="background-color: #007cc3; color:white;padding:10px; text-align: center;">Selected Transactions</th>
                <th style="background-color: #007cc3; color:white;padding:10px; text-align: center;">Total Selected Transcation Amount (₹)</th>
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

    let tableContainer = $(`<div id="group-table-container" style="max-height:500px; overflow-y:auto; scrollbar-width: none;">
  </div>`).appendTo(page.body);

    this.form = new frappe.ui.FieldGroup({
        fields: [
			{
				label: __("Use Payroll Entry"),
				fieldname: "use_payroll_entry",
				fieldtype: "Check",
				default: 0,
				change: () => {
					let usePayroll = this.form.get_value("use_payroll_entry");
					console.log(usePayroll)
					if (usePayroll == 1) {
						// Hide the Bank Account field
						this.form.set_df_property("bank", "hidden", true);
						this.form.set_df_property("bank_account", "hidden", true);
                        this.form.set_value("payroll_entry", "");
                        this.form.set_value("bank", "");
                        this.form.set_value("bank_account", "");
						// Show the Payroll Entry field
						this.form.set_df_property("payroll_entry", "hidden", false);
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision = 2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision = 2));
                        $(tableContainer).hide();
					} else {
						// Show the Bank Account field
						this.form.set_df_property("bank", "hidden", false);
						this.form.set_df_property("bank_account", "hidden", false);
                        this.form.set_value("bank", "");
                        this.form.set_value("bank_account", "");
						// Hide the Payroll Entry field
						this.form.set_df_property("payroll_entry", "hidden", true);
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision = 2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision = 2));
                        $(tableContainer).hide();
					}
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
                        this.form.refresh();
                        $(tableContainer).hide();
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision = 2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision = 2));
                    }
                    if (selectedBank && this.form.get_value("bank_account")) {
                        this.form.set_value("bank_account", "");
                        this.form.refresh();
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
					if (selectedPayrollEntry) {
						// Handle changes related to Payroll Entry field
                        this.fetchPayrollEntries(selectedPayrollEntry)
						console.log("Payroll Entry selected:", selectedPayrollEntry);
					}
                    else{
                        $(tableContainer).hide();
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
                    bankAccount = selectedBankAccount;
                    if (selectedBankAccount && !selectedBank) {
                        frappe.msgprint(__('Please select a bank before selecting a bank account.'));
                        this.form.set_value("bank_account", "");
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision = 2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision = 2));
                        $("#export-to-excel").hide();
                        this.form.refresh();
                    }
                    if (selectedBankAccount) {
                        $("#export-to-excel").removeAttr("hidden");
                        this.fetchPaymentEntries(selectedBankAccount)
                    }
                    else {
                        $(tableContainer).hide();
                        $("#export-to-excel").attr("hidden", true);
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision = 2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision = 2));
                    }
                }

            },
        ],
        body: filterContainer
    });
    this.form.make();

    $(document).on("change", ".select-all", function () {
        let isChecked = $(this).prop("checked");
        $(".group-checkbox").prop("checked", isChecked).trigger("change");
        $(".entry-checkbox").prop("checked", isChecked);
        updateTransactionSummary();
    });

    $("input").css({ "width": "auto" });
    $(".form-layout").css({ "width": "720px" });
    this.fetchPaymentEntries = function (selectedBank) {
        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment.payment.select_payment_entry",
            args: {
                bank_account: selectedBank
            },
            callback: function (response) {
                let data = response.message;
                if (!data || data.length === 0) {
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
                    thead { background-color: #007cc3; color: white; }
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
                    let status = first.workflow_state ? first.workflow_state.toLowerCase() : "";
                    let badgeStyle = getBadgeStyle(status);

                    // SUMMARY ROW (Always Visible)
                    table_html += `<tr class="group-row summary-row" data-party="${groupKey}">
                        <td style="text-align:left;">
                            ${`<span class="toggle-arrow" data-party="${groupKey}">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevron-right"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                  </span>`

                        }
                        </td>
                        <td style="text-align:left;">
                        <input type="checkbox" class="group-checkbox" data-party="${groupKey}">
                        </td>
                        <td style="text-align:left;"></td>        
                        <td style="text-align:left;">${first.party_name}</td>
                        <td style="text-align:left;"></td>
                        <td class="group-paid-amount" style="text-align:left;">${format_currency(totalAmount, 'INR', precision = 2)}</td>
                       
                        <td style="text-align:left;">
                        
                            <button style="background-color:red; padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;color:white"
                                class="cancel-btn group-cancel" data-id="${first.name}">
                                Reject
                            </button>
                        </td>
                        
                    </tr>`;

                    // CHILD ROWS (Hidden by Default)
                    payments.forEach((row, index) => {
                        table_html += `<tr class="hidden-row party-${groupKey}" style="display: none;">
                            <td></td>
                           <td class="indent">
                                <input type="checkbox" class="entry-checkbox" data-id="${row.name}" data-party="${groupKey}">
                            </td>
                            
                            <td style="text-align:left;"><a onclick="frappe.set_route('Form', 'Payment Entry', '${row.name}')">${row.name}</a></td>  <!-- ID for each child -->
                            <td style="text-align:left;">${row.party_name}</td>
                            <td style="text-align:left;">
                                ${row.remarks ? row.remarks.trim().replace(/(?:\r\n|\r|\n)/g, "<br>") : ""}
                                ${row.custom_approved_by ? "<br>" + "Approved By: " + (row.custom_approved_by || '-') : ''}
                            </td>
                            <td style="text-align:left;">${format_currency(row.base_paid_amount_after_tax, 'INR', precision = 2)}</td>
                          
                            <td style="text-align:left;">
                                <button style="background-color:red; color:white    ;padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;"
                                    class="cancel-btn" data-id="${row.name}">
                                    Reject
                                </button>
                            </td>
                             <td style="text-align:left;">
                            <button style="background-color:blue; padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;color:white"
                                class="get-details">
                                Details
                            </button>
                        </td>
                        </tr>`;
                    });
                    totalTransactions += count;
                    totalAmt += totalAmount;
                });
                $("#total-transactions").text(totalTransactions);
                $("#total-amount").text(format_currency(totalAmt.toFixed(2), 'INR', precision = 2));
                table_html += `</tbody></table>`;
                $(tableContainer).html(table_html);
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
                        // console.log('clicked---------------------')
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
        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment.payment.get_salary_slip",
            args: {
                payroll_entry: selectedPayrollEntry
            },
            callback: function (response) {
                let data = response.message;
                if (!data || data.length === 0) {
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
                    thead { background-color: #007cc3; color: white; }
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
                    let status = first.workflow_state ? first.workflow_state.toLowerCase() : "";
                    let badgeStyle = getBadgeStyle(status);

                    // SUMMARY ROW (Always Visible)
                    table_html += `<tr class="group-row summary-row" data-party="${groupKey}">
                        <td style="text-align:left;">
                            ${`<span class="toggle-arrow" data-party="${groupKey}">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevron-right"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                  </span>`

                        }
                        </td>
                        <td style="text-align:left;">
                        <input type="checkbox" class="group-checkbox" data-party="${groupKey}">
                        </td>
                        <td style="text-align:left;"></td>        
                        <td style="text-align:left;">${first.party_name}</td>
                        <td style="text-align:left;"></td>
                        <td class="group-paid-amount" style="text-align:left;">${format_currency(totalAmount, 'INR', precision = 2)}</td>
                       
                        <td style="text-align:left;">
                            <button style="background-color:red; padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;color:white"
                                class="cancel-btn group-cancel" data-id="${first.name}">
                                Reject
                            </button>
                        </td>
                        
                    </tr>`;

                    // CHILD ROWS (Hidden by Default)
                    payments.forEach((row, index) => {
                        table_html += `<tr class="hidden-row party-${groupKey}" style="display: none;">
                            <td></td>
                           <td class="indent">
                                <input type="checkbox" class="entry-checkbox" data-id="${row.name}" data-party="${groupKey}">
                            </td>
                            
                            <td style="text-align:left;"><a onclick="frappe.set_route('Form', 'Payment Entry', '${row.name}')">${row.name}</a></td>  <!-- ID for each child -->
                            <td style="text-align:left;">${row.party_name}</td>
                            <td style="text-align:left;">
                                ${row.remarks ? row.remarks.trim().replace(/(?:\r\n|\r|\n)/g, "<br>") : ""}
                                ${row.custom_approved_by ? "<br>" + "Approved By: " + (row.custom_approved_by || '-') : ''}
                            </td>
                            <td style="text-align:left;">${format_currency(row.base_paid_amount_after_tax, 'INR', precision = 2)}</td>
                          
                            <td style="text-align:left;">
                                <button style="background-color:red; color:white    ;padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;"
                                    class="cancel-btn" data-id="${row.name}">
                                    Reject
                                </button>
                            </td>
                             <td style="text-align:left;">
                            <button style="background-color:blue; padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;color:white"
                                class="get-details">
                                Details
                            </button>
                        </td>
                        </tr>`;
                    });
                    totalTransactions += count;
                    totalAmt += totalAmount;
                });
                $("#total-transactions").text(totalTransactions);
                $("#total-amount").text(format_currency(totalAmt.toFixed(2), 'INR', precision = 2));
                table_html += `</tbody></table>`;
                $(tableContainer).html(table_html);
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

                    let referenceTableRows = referenceDetails.map(item => `
                        <tr>
                            <td style="text-align:left;">${(item["Reference ID"] || "").split(",").join("<br>")}</td>
                            <td style="text-align:left;">${(item["Doctype"] || "").split(",").join("<br>")}</td>
                            <td style="text-align:left;">${(item["Approvers"] || "No Approvers").split(",").join("<br>")}</td>
                            <td style="text-align:left;">${(item["Approver Names"] || "").split(",").join("<br>")}</td>

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
                                    <td style="text-align:left;">${customDetails.custom_type || ""}</td>
                                    <td style="text-align:left;">${customDetails.custom_project_type || ""}</td>
                                    <td style="text-align:left;">${customDetails.custom_approved_by || ""}</td>
                                    <td style="text-align:left;">${customDetails.remarks || ""}</td>
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
                                    .reference-data thead {
                                        font-weight: bold;    
                                    }
                                    .section-title {
                                        font-weight: bold;
                                        font-size: 16px;
                                        margin-top: 10px;
                                        margin-bottom: 5px;
                                    }
                                </style>
    
                                <div class="section-title"></div>
                                ${referenceTableRows ?
                                    `<table class="reference-data">
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
                                    </table>`: ''}
    
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



    $(document).off("change", ".entry-checkbox").on("change", ".entry-checkbox", function () {
        let partyId = $(this).data("party");
        let allChecked = $(`.party-${partyId} .entry-checkbox`).length === $(`.party-${partyId} .entry-checkbox:checked`).length;
        $(`.group-checkbox[data-party="${partyId}"]`).prop("checked", allChecked);
        updateTransactionSummary();
    });
    $(document).off("change", ".group-checkbox").on("change", ".group-checkbox", function () {
        let partyId = $(this).data("party");
        let isChecked = $(this).prop("checked");
        $(`.party-${partyId} .entry-checkbox`).prop("checked", isChecked);
        updateTransactionSummary();
    });

    let buttonContainer = $("<div style='display: flex; justify-content: flex-start;'>")
        .appendTo(filterContainer);

    let download_excel_btn = $(`<button id='export-to-excel' style="margin-right:10px;margin-top:10px;" class="btn btn-success" hidden>Send Excel File  </button>`)
        .appendTo(buttonContainer);

    //Comment for live
    if (['hiren@mantratec.com', 'bhavyen@mantratec.com'].includes(frappe.session.user)) {
        let make_payment_btn = $(`<button style="margin-top:10px;" class="btn btn-success">Make Payment</button>`)
            .appendTo(buttonContainer);

        make_payment_btn.on('click', function () {
            let selected_entries = getSelectedEntries();
            // console.log($('.frappe-control[data-fieldname="use_payroll_entry"] input[type="checkbox"]').prop('checked'))
          

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
                outputRows.push(["", "", "", "" + format_currency(partyTotal.toFixed(2), 'INR', precision = 2)]);
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
        outputRows.push(["", "", "", "" + format_currency(partyTotal.toFixed(2), 'INR', precision = 2)]);
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

function getBadgeStyle(status) {
    if (status === "approved") {
        return "background-color: green; color: white;";
    } else if (status === "pending") {
        return "background-color: lightgray; color: black;";
    } else {
        return "background-color: red; color: white;";
    }
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
        method: "mantra_dev.api_code.banck_transaction.send_otp",
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
        method: "mantra_dev.api_code.banck_transaction.verify_otp",
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
                    method: "mantra_dev.api_code.banck_transaction.generate_payroll_payment_file",
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
                    method: "mantra_dev.api_code.banck_transaction.upload_file",
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
                            } else {
                                // If not done, you can reload or take another action
                                // window.location.reload();`
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
        let groupChildren = $(`.party-${partyId} .entry-checkbox`);
        totalTransactionCount += groupChildren.length;
        groupChildren.each(function () {
            let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
            // Remove ₹, commas, and trim
            let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

            if (!isNaN(amount)) {
                totalTransactionAmount += amount;
            }
        });
        if ($(`.group-checkbox[data-party="${partyId}"]`).prop("checked")) {
            selectedCount += groupChildren.length;
            groupChildren.each(function () {
                let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
                let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

                if (!isNaN(amount)) {
                    selectedAmount += amount;
                }
            });
        } else {
            $(`.party-${partyId} .entry-checkbox:checked`).each(function () {
                selectedCount++;
                let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
                let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

                if (!isNaN(amount)) {
                    selectedAmount += amount;
                }
            });
        }
    });
    $("#selected-count").text(selectedCount);
    $("#selected-amount").text(format_currency(selectedAmount.toFixed(2), 'INR', precision = 2));
    $("#total-transactions").text(totalTransactionCount);
    $("#total-amount").text(format_currency(totalTransactionAmount.toFixed(2), 'INR', precision = 2));
}

function getSelectedEntries() {
    let selectedEntries = new Set();
    $(".group-row").each(function () {
        let partyId = $(this).data("party");
        if ($(`.group-checkbox[data-party="${partyId}"]`).prop("checked")) {
            $(`.party-${partyId} .entry-checkbox`).each(function () {
                selectedEntries.add($(this).data("id"));
            });
        } else {
            $(`.party-${partyId} .entry-checkbox:checked`).each(function () {
                selectedEntries.add($(this).data("id"));
            });
        }
    });
    return Array.from(selectedEntries);
}