frappe.pages['payment-page-approve'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Payment Page Approver',
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
                <td style="text-align:center; padding:10px;font-size:16px;"><span id="total-amount">${(format_currency(0, 'INR', precision=2))}</span></td>
                <td style="text-align:center; padding:10px;font-size:16px;"><span id="selected-count">0</span></td>
                <td style="text-align:center; padding:10px;font-size:16px;"><span id="selected-amount">${(format_currency(0, 'INR', precision=2))}</span></td>
            </tr>
        </tbody>
    </table>`).appendTo(page.body); 

    let tableContainer = $(`<div id="group-table-container" style="max-height:500px; overflow-y:auto; scrollbar-width: none;">
  </div>`).appendTo(page.body);

    this.form = new frappe.ui.FieldGroup({
        fields: [
            {
                label: __("Bank"),
                fieldname: "bank",
                fieldtype: "Link",
                options: "Bank",
                reqd:1,
                change: () => {
                    let selectedBank = this.form.get_value("bank");
                    bank=selectedBank;
                    if(!selectedBank){
                        this.form.set_value("bank_account", ""); 
                        this.form.refresh();
                        $(tableContainer).hide();
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision=2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision=2));
                    }
                    if(selectedBank && this.form.get_value("bank_account")){
                        this.form.set_value("bank_account", ""); 
                        this.form.refresh();
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
                reqd:1,
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
                    bankAccount=selectedBankAccount;
                    if (selectedBankAccount && !selectedBank) {
                        frappe.msgprint(__('Please select a bank before selecting a bank account.'));
                        this.form.set_value("bank_account", ""); 
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision=2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision=2));
                        $("#export-to-excel").hide();
                        this.form.refresh();
                    } 
                    if(selectedBankAccount){
                        $("#export-to-excel").removeAttr("hidden");
                         this.fetchPaymentEntries(selectedBankAccount)
                    }
                    else{
                        $(tableContainer).hide();
                        $("#export-to-excel").attr("hidden", true);
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision=2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision=2));
                    }
                }
               
            }
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
    
    $("input").css({"width": "auto"});
    $(".form-layout").css({"width": "490px"});
    this.fetchPaymentEntries = function(selectedBank) {
        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment_page_approve.payment_page_approve.select_payment_entry",
            args: {
                bank_account: selectedBank
            },
            callback: function(response) {
                let data = response.message;
                if (!data || data.length === 0) {
                    $(tableContainer).html('<p style="text-align: center; font-size: 16px; color: red;">No Payment Entry Found</p>');
                    $("#total-transactions").text(0);
                    $("#total-amount").text(format_currency(0, 'INR', precision=2));
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
                            <th style="text-align:left;">Reference No</th>
                            <th style="text-align:left;">Total Paid Amount</th>
                            <th style="text-align:left;">Status</th>
							<th style="text-align:left;">On Hold</th>
							<th style="text-align:left;">Approve Action</th>
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
                            ${
                                 `<span class="toggle-arrow" data-party="${groupKey}">
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
                        <td class="group-paid-amount" style="text-align:left;">${format_currency(totalAmount, 'INR', precision=2)}</td>
                       
                        <td style="text-align:left;">
                            <span style="${badgeStyle} padding: 5px 15px; font-size: 14px; border-radius: 20px;">
                                ${first.workflow_state || ""}
                            </span>
                        </td>
                        <td style="text-align:left;">
                                <button style="background-color:orange; color:white;padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;"
                                    class="hold-btn group-hold" data-id="${first.name}">
                                    Hold
                                </button>
                        </td>
						<td style="text-align:left;">
                                <button style="background-color:green; color:white    ;padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;"
                                    class="approve-btn group-approve" data-id="${first.name}">
                                    Approve
                                </button>
                        </td>
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
                            <td style="text-align:left;">${row.reference_no}</td>
                            <td style="text-align:left;">${format_currency(row.base_paid_amount_after_tax, 'INR', precision=2)}</td>
                          
                            <td style="text-align:left;">
                                <span style="${getBadgeStyle(row.workflow_state.toLowerCase())} padding: 5px 15px; font-size: 14px; border-radius: 20px;">
                                    ${row.workflow_state || ""}
                                </span>
                            </td>
                            <td style="text-align:left;">
                                <button style="background-color:orange; color:white;padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;"
                                    class="hold-btn" data-id="${row.name}">
                                    Hold
                                </button>
                            </td>
							 <td style="text-align:left;">
                                <button style="background-color:green; color:white    ;padding: 5px 15px; font-size: 14px; border-radius: 6px; border: 0px;"
                                    class="approve-btn" data-id="${row.name}">
                                    Approve
                                </button>
                            </td>
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
                $("#total-amount").text(format_currency(totalAmt.toFixed(2), 'INR', precision=2));
                table_html += `</tbody></table>`;
                $(tableContainer).html(table_html);
                $(".toggle-arrow").on("click", function() {
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
                $(document).off("click", ".hold-btn").on("click", ".hold-btn", function () {
					console.log("clicked")
                    let $btn = $(this);
                    let $row = $btn.closest("tr");
                    let paymentEntryId = $btn.data("id");
                    let partyId = $row.closest(".group-row").data("party");
                    if ($btn.hasClass("group-hold")) {
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
                        holdPaymentEntry(allIds, function (success) {
                            if (success) {
                                $row.remove(); 
                                $(`.party-${partyId}`).remove(); 
                                updateTransactionSummary();
                            }
                        });
                    } 
                    else {
                        partyId = $row.find(".entry-checkbox").data("party");
                        holdPaymentEntry([paymentEntryId], function (success) {
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
				$(document).off("click", ".approve-btn").on("click", ".approve-btn", function () {
                    let $btn = $(this);
                    let $row = $btn.closest("tr");
                    let paymentEntryId = $btn.data("id");
                    let partyId = $row.closest(".group-row").data("party");
                    if ($btn.hasClass("group-approve")) {
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
                        approvePaymentEntry(allIds, function (success) {
                            if (success) {
                                $row.remove(); 
                                $(`.party-${partyId}`).remove(); 
                                updateTransactionSummary();
                            }
                        });
                    } 
                    else {
                        partyId = $row.find(".entry-checkbox").data("party");
                        approvePaymentEntry([paymentEntryId], function (success) {
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
                if(data.length !== 0){
                    $(tableContainer).show();
                }
                else{
                    $("#export-to-excel").attr("hidden", true);
                }
               
            }
        });
    };

    
    $(document).on('click', '.get-details', function() {
        let paymentEntryId = $(this).closest('tr').find('td a').text().trim();
    
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
    });
    
    
      
    $(document).off("change", ".entry-checkbox").on("change", ".entry-checkbox", function() {
        let partyId = $(this).data("party");
        let allChecked = $(`.party-${partyId} .entry-checkbox`).length === $(`.party-${partyId} .entry-checkbox:checked`).length;
        $(`.group-checkbox[data-party="${partyId}"]`).prop("checked", allChecked);
        updateTransactionSummary();
    });
    $(document).off("change", ".group-checkbox").on("change", ".group-checkbox", function() {
        let partyId = $(this).data("party");
        let isChecked = $(this).prop("checked");
        $(`.party-${partyId} .entry-checkbox`).prop("checked", isChecked);
        updateTransactionSummary();
    });

    let buttonContainer = $("<div style='display: flex; justify-content: flex-start;'>")
    .appendTo(filterContainer);

    let download_excel_btn = $(`<button id='export-to-excel' style="margin-right:10px;margin-top:10px;" class="btn btn-success" hidden>Send Excel File  </button>`)
        .appendTo(buttonContainer);
    
    $(document).on('click', '#export-to-excel', function () {
        // Create a new Frappe Dialog for selecting a user email
        let d = new frappe.ui.Dialog({
            title: 'Select User to Send Email',
            fields: [
                {
                    label: 'User Email',
                    fieldname: 'user_email',
                    fieldtype: 'Link',
                    options:'User'
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
        tableClone.find('th:nth-child(6), td:nth-child(6)').remove();
		tableClone.find('th:nth-child(7), td:nth-child(7)').remove();
		tableClone.find('th:nth-child(8), td:nth-child(8)').remove();
		tableClone.find('th:nth-last-child(2), td:nth-last-child(2)').remove();
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
                    outputRows.push(["", "", "", "" + format_currency(partyTotal.toFixed(2), 'INR', precision=2)]);
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
            outputRows.push(["", "", "", "" + format_currency(partyTotal.toFixed(2), 'INR', precision=2)]);
        }
        ws_data = ws_data.concat(outputRows); 
        let ws = XLSX.utils.aoa_to_sheet(ws_data);
        ws['!cols'] = [
            { wch: 20 },  // width for ID column
            { wch: 30 },  // width for Party column
            { wch: 25 },  // width for Reference No column
            { wch: 20 }   // width for Total Paid Amount column
        ];
        XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
        let workbookOutput = XLSX.write(wb, { bookType: 'xlsx', type: 'binary' });
        $('.hidden-row').css('display', 'none');
        let base64File = btoa(workbookOutput);

        //Use frappe.call to send the email with the Excel file attachment
        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment_page.payment_page.send_excel_email",  // Update with your app's path
            args: {
                user_email: selectedUser,
                filename: "payment_data.xlsx",
                filedata: base64File,
                subject: "Payment Entry Details"
            },
            callback: function(response) {
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
    groupRow.find(".group-paid-amount").text(format_currency(totalPaidAmount.toFixed(2), 'INR', precision=2)); 
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
            method: "mantra_dev.mantra_dev.page.payment_page.payment_page.cancel_payment_entries",
            args: {
                payment_entry_ids: paymentEntryIds
            },
            callback: function(response) {
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
function holdPaymentEntry(paymentEntryIds, callback) {
	frappe.call({
		method: "mantra_dev.mantra_dev.page.payment_page_approve.payment_page_approve.hold_payment_entries",
		args: {
			payment_entry_ids: paymentEntryIds
		},
		callback: function(response) {
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
function approvePaymentEntry(paymentEntryIds, callback) {
	frappe.call({
		method: "mantra_dev.mantra_dev.page.payment_page_approve.payment_page_approve.approve_payment_entries",
		args: {
			payment_entry_ids: paymentEntryIds
		},
		callback: function(response) {
			if (response.message === "Success") {
				updateTransactionSummary()
				callback(true); 
			} else {
				frappe.msgprint(__('Failed to Approve payment entries.'));
				callback(false); 
			}
		}
	});
}

            
function removeSelectedRows() {
    $("input[type='checkbox']:checked").closest("tr").remove();
}
function updateTransactionSummary() {
    let selectedCount = 0;
    let selectedAmount = 0;
    let totalTransactionCount = 0;
    let totalTransactionAmount = 0;
    $(".group-row").each(function() {
        let partyId = $(this).data("party");
        let groupChildren = $(`.party-${partyId} .entry-checkbox`);
        totalTransactionCount += groupChildren.length;
        groupChildren.each(function() {
            let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
            // Remove ₹, commas, and trim
            let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());
    
            if (!isNaN(amount)) {
                totalTransactionAmount += amount;
            }
        });
        if ($(`.group-checkbox[data-party="${partyId}"]`).prop("checked")) {
            selectedCount += groupChildren.length;
            groupChildren.each(function() {
                let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
                let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());
    
                if (!isNaN(amount)) {
                    selectedAmount += amount;
                }
            });
        } else {
            $(`.party-${partyId} .entry-checkbox:checked`).each(function() {
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
    $("#selected-amount").text(format_currency(selectedAmount.toFixed(2), 'INR', precision=2));
    $("#total-transactions").text(totalTransactionCount);
    $("#total-amount").text(format_currency(totalTransactionAmount.toFixed(2), 'INR', precision=2));
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