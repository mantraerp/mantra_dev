frappe.pages['payment-page-approve'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Payment Page Approver',
        single_column: true
    });
    frappe.breadcrumbs.add("", "");
    let filterContainer = $('<div class="filter-container" style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; justify-content: space-between;"></div>').appendTo(page.body);

    let transaction_summary_table = $(`<table id="transaction-summary-table" style="margin-bottom: 20px; width: 100%; border-collapse: collapse;font-family: var(--font-stack);">
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

    let tableContainer = $(`<div id="group-table-container" style="max-height:500px; overflow-y:auto; scrollbar-width: none;">
  </div>`).appendTo(page.body);

    this.form = new frappe.ui.FieldGroup({
        fields: [
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
                        $("#export-to-excel").attr("hidden", true);
                        $("#total-transactions").text(0);
                        $("#total-amount").text(format_currency(0, 'INR', precision = 2));
                        $("#selected-count").text(0);
                        $("#selected-amount").text(format_currency(0, 'INR', precision = 2));
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

    $("input").css({ "width": "auto" });
    $(".form-layout").css({ "width": "490px" });
    this.fetchPaymentEntries = function (selectedBank) {
        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment_page_approve.payment_page_approve.select_payment_entry",
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
                let totalTransactions = 0;
                let totalAmt = 0;
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
                    thead { background-color: var(--subtle-fg); color: var(--text-color) !important;}
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
							<th style="text-align:left;">On Hold</th>
							<th style="text-align:left;">Approve Action</th>
                            <th style="text-align:left;">Action</th>
                            <th style="text-align:left;">Details</th>
                             <th style="text-align:left;">New Details</th>
                        </tr>
                    </thead>
                    <tbody>`;
                // Initialize total variables before the loop

                Object.keys(groupedData).forEach(groupKey => {
                    let group = groupedData[groupKey];
                    let payments = group.entries;
                    let totalAmount = group.total_amount;
                    let count = payments.length;

                    let first = payments[0]; // Use the first row for summary
                    let status = first.workflow_state ? first.workflow_state.toLowerCase() : "";
                    let badgeStyle = getBadgeStyle(status);
                    totalTransactions += count;
                    totalAmt += totalAmount;


                    if (count === 1) {
                        // If only one entry, display as a normal row
                        let row = payments[0];
                        table_html += `
                        <tr class="group-row">
                            <td></td>
                            <td style="text-align:left;">
                                <input type="checkbox" class="entry-checkbox" data-id="${row.name}">
                            </td>
                            <td style="text-align:left;">
                                <a onclick="frappe.set_route('Form', 'Payment Entry', '${row.name}')">${row.name}</a>
                            </td>
                            <td style="text-align:left;">${row.party_name}</td>
                            <td style="text-align:left;">
                                ${row.remarks ? row.remarks.trim().replace(/(?:\r\n|\r|\n)/g, "<br>") : ""}
                                ${row.approver_names ? "<br>Approved By: " + row.approver_names : ''}
                            </td>
                            <td style="text-align:left;">${format_currency(row.base_paid_amount_after_tax, 'INR', 2)}</td>
                            <td style="text-align:left;">
                                <button class="hold-btn btn btn-secondary" data-id="${row.name}" >
                                    Hold
                                </button>
                            </td>
                            <td style="text-align:left;">
                                <button class="approve-btn btn btn-secondary" data-id="${row.name}" >
                                    Approve
                                </button>
                            </td>
                            <td style="text-align:left;">
                                <button class="cancel-btn btn btn-secondary" data-id="${row.name}" >
                                    Reject
                                </button>
                            </td>
                              <td>
                                <button 
                                    class="get-details btn btn-primary">
                                    Details
                                </button>
                            </td>
                            <td>
                                <button 
                                    class="get-details-new btn btn-primary">
                                    New Details
                                </button>
                            </td>
                        </tr>`;
                    } else {
                        // If multiple entries, display collapsible rows
                        let first = payments[0]; // Use first row for summary

                        table_html += `
                        <tr class="group-row summary-row" data-party="${groupKey}">
                            <td style="text-align:left;">
                                <span class="toggle-arrow" data-party="${groupKey}">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <polyline points="9 18 15 12 9 6"></polyline>
                                    </svg>
                                </span>
                            </td>
                            <td style="text-align:left;">
                                <input type="checkbox" class="group-checkbox" data-party="${groupKey}">
                            </td>
                            <td style="text-align:left;"></td>        
                            <td style="text-align:left;">${first.party_name}</td>
                            <td style="text-align:left;"></td>
                            <td class="group-paid-amount" style="text-align:left;">${format_currency(totalAmount, 'INR', 2)}</td>
                            <td style="text-align:left;">
                                <button class="hold-btn group-hold btn btn-secondary" data-id="${first.name}" >
                                    Hold
                                </button>
                            </td>
                            <td style="text-align:left;">
                                <button class="approve-btn group-approve btn btn-secondary" data-id="${first.name}" >
                                    Approve
                                </button>
                            </td>
                            <td style="text-align:left;">
                                <button class="cancel-btn group-cancel btn btn-secondary" data-id="${first.name}" >
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
                                ${row.approver_names ? "<br>" + "Approved By: " + (row.approver_names || '-') : ''}
                            </td>
                            <td style="text-align:left;">${format_currency(row.base_paid_amount_after_tax, 'INR', precision = 2)}</td>
                            <td style="text-align:left;">
                                <button 
                                    class="hold-btn btn btn-secondary" data-id="${row.name}">
                                    Hold
                                </button>
                            </td>
							 <td style="text-align:left;">
                                <button 
                                    class="approve-btn btn btn-secondary" data-id="${row.name}">
                                    Approve
                                </button>
                            </td>
                            <td style="text-align:left;">
                                <button 
                                    class="cancel-btn btn btn-secondary" data-id="${row.name}">
                                    Reject
                                </button>
                            </td>
                             <td style="text-align:left;">
                            <button
                                class="get-details btn btn-primary">
                                Details
                            </button>
                        </td>
                          <td style="text-align:left;">
                            <button
                                class="get-details-new btn btn-primary">
                                New Details
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
                $(document).off("click", ".hold-btn").on("click", ".hold-btn", function () {
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
                if (data.length !== 0) {
                    $(tableContainer).show();
                }
                else {
                    $("#export-to-excel").attr("hidden", true);
                }

            }
        });
    };

    $(document).on('click', '.get-details-new', function () {
        frappe.dom.freeze(__("Fetching Details..."));
        let paymentEntryId = $(this).closest('tr').find('td a').text().trim();

        if (!paymentEntryId) {
            frappe.msgprint(__('Payment Entry ID not found.'));
            return;
        }

        frappe.call({
            method: "mantra_dev.mantra_dev.page.payment.payment.get_payment_entry_reference_details",
            args: { payment_entry: paymentEntryId },
            callback: function (r) {
                frappe.dom.unfreeze();

                if (!r.message) return;
                if (r.message.error) {
                    frappe.msgprint(r.message.error);
                    return;
                }

                let referenceDetails = r.message.reference_details || [];
                let customDetails = r.message.custom_details || {};

                const pivotDoctypes = [
                    "Material Request",
                    "Purchase Order",
                    "Purchase Invoice",
                    "Purchase Receipt"
                ];

                const advanceDoctypes = ["Expense Claim", "Employee Advance"];

                let pivotDocs = [], advanceDocs = [];

                referenceDetails.forEach(ref => {
                    if (advanceDoctypes.includes(ref.doctype)) {
                        advanceDocs.push(ref);
                    } else {
                        pivotDocs.push(ref);
                    }
                });

                let pivotRows = "";
                if (pivotDocs.length) {
                    let groupedRows = [];
                    pivotDocs.forEach(ref => {
                        let placed = false;
                        for (const group of groupedRows) {
                            if (!group[ref.doctype]) {
                                group[ref.doctype] = ref;
                                placed = true;
                                break;
                            }
                        }
                        if (!placed) {
                            const newRow = {};
                            newRow[ref.doctype] = ref;
                            groupedRows.push(newRow);
                        }
                    });



                    for (const row of groupedRows) {
                        pivotRows += "<tr>";
                        for (const dt of pivotDoctypes) {
                            const item = row[dt];
                            if (item) {
                                const docLink = `<a href="/app/${dt.toLowerCase().replace(/ /g, "-")}/${item.Document}" target="_blank">${item.Document}</a>`;
                                const attachments = item.Attachments
                                    ? item.Attachments.split(',').map(url => `<a href="${url}" target="_blank">${url}</a>`).join("<br>")
                                    : "";

                                const poButton = (dt === "Purchase Order" && item["Po Approval"])
                                    ? `<button class="btn btn-primary btn-sm po-details-btn" data-docname="${item['Document']}" data-po="${item["Po Approval"]}">PO Details</button><br>`
                                    : "";

                                pivotRows += `
                                    <td style="text-align:left;">
                                        <div style="margin-bottom:8px;">
                                            <b style="font-size:15px;">${docLink}</b><br>
                                            <small><b>Created:</b> ${item["Created On"] || "-"}</small><br>
                                            <small><b>Submitted:</b> ${item["Submitted On"] || "-"}</small><br>
                                        </div>
                                        ${item["Purpose"] ? `<div style="margin-bottom:8px;font-size:15px;"><small><b>Purchase Remark:</b> ${item["Purpose"]}</small></div>` : ""}
                                        <div style="margin-bottom:8px;">
                                            <small><b>Approvers:</b></small><br>
                                            <div style="font-size:15px; color: var(--text-color) !important">${item["Approvers"] || "No Approvers"}</div>
                                        </div>
                                        ${dt === "Purchase Invoice" && attachments ? `<div style="margin-bottom:8px;"><small><b>Attachments:</b></small><br><div style="font-size:15px;">${attachments}</div></div>` : ""}
                                        ${poButton}
                                    </td>
                                `;


                                if (dt === "Purchase Order" || dt === "Purchase Invoice") {
                                    pivotRows += `<td style="vertical-align: top;">${format_currency((item['Amount'] || 0).toFixed(2), 'INR', 2)}</td>`;
                                }

                            } else {

                                pivotRows += `<td></td>`;
                                if (dt === "Purchase Order" || dt === "Purchase Invoice") {
                                    pivotRows += `<td></td>`;
                                }
                            }
                        }
                        pivotRows += "</tr>";
                    }
                }

                let advanceRows = "";
                if (advanceDocs.length) {
                    let advanceGrouped = [];
                    advanceDocs.forEach(ref => {
                        let placed = false;
                        for (const group of advanceGrouped) {
                            if (!group[ref.doctype]) {
                                group[ref.doctype] = ref;
                                placed = true;
                                break;
                            }
                        }
                        if (!placed) {
                            const newRow = {};
                            newRow[ref.doctype] = ref;
                            advanceGrouped.push(newRow);
                        }
                    });

                    for (const row of advanceGrouped) {
                        advanceRows += "<tr>";
                        for (const dt of advanceDoctypes) {
                            const item = row[dt];
                            if (item) {
                                const docLink = `<a href="/app/${dt.toLowerCase().replace(/ /g, '-')}/${item.Document}" target="_blank">${item.Document}</a>`;
                                advanceRows += `
                                    <td style="text-align:left;">
                                        <b>${docLink}</b><br>
                                        <small><b>Created:</b> ${item["Created On"] || "-"}</small><br>
                                        <small><b>Submitted:</b> ${item["Submitted On"] || "-"}</small><br>
                                           <small><b>Amount:</b> ${format_currency((item['Amount'] || 0).toFixed(2), 'INR', 2) || "-"}</small><br>
                                        <small><b>Purpose:</b> ${item.Purpose || ""}</small><br>
                                        <small><b>Approvers:</b></small><br>
                                        <div style="font-size:15px; color: #ccc;">${item.Approvers || "No Approvers"}</div>
                                    </td>`;
                            } else {
                                advanceRows += `<td></td>`;
                            }
                        }
                        advanceRows += "</tr>";
                    }
                }

                let customDetailsTable = `
                    <table class="custom-details-table">
                        <thead>
                            <tr><th>Type</th><th>Project Type</th><th>Approved By</th><th>Payment Remark</th></tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="text-align:left;">${customDetails.custom_type || ""}</td>
                                <td style="text-align:left;">${customDetails.custom_project_type || ""}</td>
                                <td style="text-align:left;">${customDetails.custom_approved_by || ""}</td>
                                <td style="text-align:left;" rowspan="2">
                                    <div class="remark-text">
                                        <strong>Remark:</strong><br>
                                        <p>${customDetails.remarks || "No Remark"}</p>
                                        <hr style="margin:3px 0; border: 0; border-top: 1px solid #ccc;">
                                        ${customDetails.custom_management_remarks ? `<strong>Approver Remark:</strong><br><p>${customDetails.custom_management_remarks}</p>` : ''}
                                        <button style="float:left;margin-top:5px;" class="btn btn-primary btn-sm update-remark-btn" 
                                            data-payment-entry="${customDetails.name}" 
                                            data-remark="${(customDetails.remarks + (customDetails.custom_management_remarks || '')) || ''}"
                                            data-previous-remark="${customDetails.remarks || ''}"   
                                            data-management-remark="${customDetails.custom_management_remarks || ''}">
                                            Update Remark
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <br>
                    <table class="custom-details-table">
                        <thead><tr><th>Unallocated Amount</th></tr></thead>
                        <tbody>
                            <tr><td style="text-align:left;">${format_currency((customDetails.unallocated_amount || 0).toFixed(2), 'INR', 2)}</td></tr>
                        </tbody>
                    </table>
                `;

                let htmlContent = `
                    <style>
                        .reference-pivot {
                            border-collapse: collapse;
                            width: 100%;
                            font-size: 15px;
                        }
                        .reference-pivot th, .reference-pivot td,
                        .custom-details-table th, .custom-details-table td {
                            padding: 10px;
                            border: 1px solid #ccc;
                            text-align: left;
                            vertical-align: top;
                             font-size: 15px;
                        }
                        .reference-pivot th {
                            background-color: var(--subtle-fg);
                        }
                        small{
                        font-size:15px;}
                        .section-title {
                            font-weight: bold;
                            font-size: 16px;
                            margin-top: 10px;
                            margin-bottom: 5px;
                        }
                    </style>
                `;

                if (pivotRows) {
                    htmlContent += `
                        <div class="section-title">Reference Details</div>
                        <table class="reference-pivot">
                            <thead>
                               <tr>
                                    <th>Material Request</th>
                                    <th>Purchase Order</th>
                                    <th>Purchase Order Amount</th>
                                    <th>Purchase Invoice</th>
                                    <th>Purchase Invoice Amount</th>
                                    <th>Purchase Receipt</th>
                                </tr>
                            </thead>
                            <tbody>${pivotRows}</tbody>
                        </table>
                        <br>
                    `;
                }

                if (advanceRows) {
                    htmlContent += `
                        <div class="section-title">Reference Details</div>
                        <table class="reference-pivot">
                            <thead>
                                <tr><th>Expense Claim</th><th>Employee Advance</th></tr>
                            </thead>
                            <tbody>${advanceRows}</tbody>
                        </table>
                        <br>
                    `;
                }

                htmlContent += customDetailsTable;

                let d = new frappe.ui.Dialog({
                    title: __("Approval Details"),
                    size: "extra-large",
                    fields: [{
                        fieldtype: "HTML",
                        options: htmlContent
                    }]
                });

                d.show();
            }
        });
    });




    $(document).on('click', '.get-details', function () {
        frappe.dom.freeze(__("Fetching Details..."));
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
                    frappe.dom.unfreeze();
                    if (r.message.error) {
                        frappe.msgprint(r.message.error);
                        return;
                    }

                    let referenceDetails = r.message.reference_details || [];
                    let customDetails = r.message.custom_details || {};

                    let referenceTableRows = referenceDetails.map(item => {
                        let attachmentColumn = "";


                        if (item["doctype"] === "Purchase Order" && item["Po Approval"]) {
                            attachmentColumn += ` <button class="btn btn-primary btn-sm po-details-btn" data-docname="${item['Document']}" data-po="${item["Po Approval"]}">
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
                                item['Attachments'] ?
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
                                    <th>Payment Remark</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="text-align:left;">${customDetails.custom_type || ""}</td>
                                    <td style="text-align:left;">${customDetails.custom_project_type || ""}</td>
                                    <td style="text-align:left;">${customDetails.custom_approved_by || ""}</td>
                                    <td style="text-align:left;" rowspan="2">
                                        <div class="remark-text">
                                            <strong>Remark:</strong><br>
                                            <p>${customDetails.remarks || "No Remark"}</p>
                                            <hr style="margin:3px 0; border: 0; border-top: 1px solid #ccc;">
                                            ${customDetails.custom_management_remarks ? `<strong>Approver Remark:</strong><br>
                                            <p>${customDetails.custom_management_remarks || ""}</p>` : ''}
                                            <button style="float:left;margin-top:5px;" class="btn btn-primary btn-sm update-remark-btn" 
                                            data-payment-entry="${customDetails.name}" 
                                            data-remark="${(customDetails.remarks + (customDetails.custom_management_remarks ? customDetails.custom_management_remarks : '')) || ''}"
                                            data-previous-remark="${customDetails.remarks || ''}"   
                                            data-management-remark = "${customDetails.custom_management_remarks || ''}">
                                            Update Remark
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                         <br>
                         <table class="custom-details-table">
                            <thead>
                                <tr>
                                    <th>Unallocated Amount</th>
                                   
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                <td style="text-align:left;">${format_currency(customDetails.unallocated_amount.toFixed(2), 'INR', precision = 2) || ""}</td>
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
                                            <th>Purchase Remark</th>
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

    // $(document).on("click", ".po-details-btn", function () {
    //     let poId = $(this).data("po");
    //     if (poId) {
    //         frappe.open_in_new_tab = true;
    //         frappe.set_route("Form", "PO Form Approval", poId);
    //     }
    //     else{
    //        frappe.msgprint('Po Form Approval is not Found')
    //     }
    // });

    $(document).on("click", ".po-details-btn", async function () {
        let poId = $(this).data("docname");
        if (poId) {


            try {
                // Fetch document details via Frappe backend
                let response = await new Promise((resolve, reject) => {
                    frappe.call({
                        method: "mantra.backend_code.detail_popup.fetch_document_details",
                        args: {
                            doctype: "Purchase Order",
                            docname: poId
                        },
                        callback: function (r) {

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
                    size: 'extra-large',
                    primary_action_label: __("Close"),
                    primary_action: () => d.hide()
                });

                d.show();
            } catch (error) {
                console.error(error);
                frappe.msgprint(__("Failed to fetch purchase order details"));
            }
        }
    }
    );

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

    let download_excel_btn = $(`<button id='export-to-excel' style="margin-right:10px;margin-top:10px;" class="btn btn-primary" hidden>Send Excel File  </button>`)
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
    tableClone.find('th:nth-child(6), td:nth-child(6)').remove();
    tableClone.find('th:nth-child(7), td:nth-child(7)').remove();
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

    //Use frappe.call to send the email with the Excel file attachment
    frappe.call({
        method: "mantra_dev.mantra_dev.page.payment_page.payment_page.send_excel_email",  // Update with your app's path
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
$(document).on('click', '.update-remark-btn', function () {
    let paymentEntryId = $(this).data('payment-entry');
    let currentRemark = $(this).data('remark');
    let previousRemark = $(this).data('previous-remark')
    let remarkTextSpan = $(this).closest('tr').find('.remark-text');
    let management_remark = $(this).data('management-remark');

    let updateDialog = new frappe.ui.Dialog({
        title: __("Update Remark"),
        fields: [
            {
                fieldname: 'remark',
                fieldtype: 'Small Text',
                label: 'Remark',
                default: management_remark ? management_remark : currentRemark
            }
        ],
        primary_action_label: 'Submit',
        primary_action(values) {
            frappe.call({
                method: "mantra_dev.mantra_dev.page.payment_page_approve.payment_page_approve.update_payment_entry_remark",
                args: {
                    payment_entry: paymentEntryId,
                    remark: values.remark
                },
                callback: function (r) {
                    if (r.message === 'success') {
                        frappe.msgprint(__('Remark updated successfully.'));
                        if (remarkTextSpan) {
                            remarkTextSpan.html('')
                            remarkTextSpan.html(" <strong>Remark: </strong><p>" + previousRemark + "</p><hr style='margin:10px 0; border: 0; border-top: 1px solid #ccc;'>" + "<strong>Approver Remark: </strong><p>" + values.remark + "</p>")
                            remarkTextSpan.append(
                                "<button style='float:left; margin-top:5px; margin-right:5px;' class='btn btn-primary btn-sm update-remark-btn' " +
                                "data-payment-entry='" + paymentEntryId + "' " +
                                "data-remark='" + ((currentRemark) || '') + "' " +
                                "data-previous-remark='" + (previousRemark || '') + "' " +
                                "data-management-remark='" + (values.remark ? values.remark : currentRemark || '') + "'>" +
                                "Update Remark</button>"
                            );
                        }
                        updateDialog.hide();
                    } else {
                        frappe.msgprint(__('Failed to update remark.'));
                    }
                }
            });
        }
    });

    updateDialog.show();
});
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
function holdPaymentEntry(paymentEntryIds, callback) {
    frappe.call({
        method: "mantra_dev.mantra_dev.page.payment_page_approve.payment_page_approve.hold_payment_entries",
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
function approvePaymentEntry(paymentEntryIds, callback) {
    frappe.call({
        method: "mantra_dev.mantra_dev.page.payment_page_approve.payment_page_approve.approve_payment_entries",
        args: {
            payment_entry_ids: paymentEntryIds
        },
        callback: function (response) {
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

function updateTransactionSummary() {
    let selectedCount = 0;
    let selectedAmount = 0;
    let totalTransactionCount = 0;
    let totalTransactionAmount = 0;

    $(".group-row").each(function () {
        let partyId = $(this).data("party");
        let groupCheckbox = $(`.group-checkbox[data-party="${partyId}"]`);
        let groupChildren = $(`.party-${partyId} .entry-checkbox`);

        // If the party has only one entry, it won't have child rows
        if (groupChildren.length === 0) {
            totalTransactionCount++;
            let amountText = $(this).find("td:nth-child(6)").text();
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
            // Multiple transactions under a group
            totalTransactionCount += groupChildren.length;
            groupChildren.each(function () {
                let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
                let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

                if (!isNaN(amount)) {
                    totalTransactionAmount += amount;
                }
            });

            if (groupCheckbox.prop("checked")) {
                selectedCount += groupChildren.length;
                groupChildren.each(function () {
                    let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
                    let amount = parseFloat(amountText.replace('₹', '').replace(/,/g, '').trim());

                    if (!isNaN(amount)) {
                        selectedAmount += amount;
                    }
                });
            } else {
                // Count only selected child rows if the group is not checked
                groupChildren.filter(":checked").each(function () {
                    selectedCount++;
                    let amountText = $(this).closest("tr").find("td:nth-child(6)").text();
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
