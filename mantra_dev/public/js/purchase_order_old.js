frappe.ui.form.on("Purchase Order", {
    onload: function (frm) {
        // if (frm.doc.docstatus !== 1 && !frm.doc.custom_purchase_person) {
        //     frappe.call({
        //         method : 'mantra_dev.overrides.purchase_order.get_purchase_person',
        //         callback : function(r){
        //             if(r.message){
        //                 frm.set_value('custom_purchase_person', r.message);
        //             }
        //         }
        //     });
        // }
        frm.set_query("set_warehouse", () => {
            return {
                filters: {
                    custom_is_purchase_warehouse: 1,
                },
            };
        });
        frm.set_query("set_from_warehouse", () => {
            return {
                filters: {
                    custom_is_purchase_warehouse: 1,
                },
            };
        });
        frm.set_query("supplier_warehouse", () => {
            return {
                filters: {
                    custom_is_subcontracting_warehouse: 1,
                },
            };
        });
        setTimeout(() => {
            frm.set_query("supplier", () => {
                return {
                    filters: {
                        workflow_state: "Approved",
                    },
                };
            });
        }, 1000); // 1000 milliseconds = 1 second
        if (frappe.user_roles.includes("System Manager") == false) {
            setTimeout(() => {
                frm.remove_custom_button("Update Items");
            }, 0);
        }
    },
    refresh: function (frm) {
        // To show details
        frm.add_custom_button(("Details"), async () => {
            let po = frm.doc;
    
            async function getStockDetails(item_code, warehouse) {
                return new Promise((resolve, reject) => {
                    frappe.call({
                        method: "mantra_dev.backend_code.purchase_order.purchase_order.get_stock_details",
                        args: {
                            item_code: item_code,
                            warehouse: warehouse
                        },
                        callback: function (r) {
                            if (!r.exc) {
                                console.log(r.message);
                                resolve(r.message);
                            } else {
                                reject("Error fetching stock data");
                            }
                        }
                    });
                });
            }
    
            let itemStockPromises = (po.items || []).map(async (item) => {
                let stockDetails = await getStockDetails(item.item_code, item.warehouse);
                return {
                    ...item,
                    available_qty_in_target: stockDetails.available_qty_in_target,
                    total_available_stock: stockDetails.total_available_stock
                };
            });
    
            let itemsWithStock = await Promise.all(itemStockPromises);
    
            let po_form_details = await new Promise((resolve, reject) => {
                frappe.call({
                    method: "mantra_dev.backend_code.purchase_order.purchase_order.get_po_form_details",
                    args: {
                        purchase_order_id: frm.doc.name
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            resolve(r.message);
                        } else {
                            reject("Error fetching po form details");
                        }
                    }
                });
            });

            let hasStockDetails = po_form_details && po_form_details.stock_detail && po_form_details.stock_detail.length > 0;

            // Construct HTML content
            let html = `
                <div>
                    <h4>${po.name}</h4>
                    <p><strong>Supplier Name:</strong> ${po.supplier_name}</p>
                    <p><strong>Status:</strong> ${po.status}</p>
                    <p><strong>Grand Total:</strong> ${po.grand_total}</p>
                    <h5>Items:</h5>
                    <table class="table table-bordered item-stock">
                        <thead>
                            <tr>
                                <th>Item Name</th>
                                <th>Qty</th>
                                <th>Rate</th>
                                <th>Target Warehouse Qty</th>
                                <th>Total Qty</th>
                                ${hasStockDetails ? `<th>Demand</th><th>Additional</th>` : ""}
                            </tr>
                        </thead>
                        <tbody>
                            ${itemsWithStock.map(item => {
                                let stockDetail = hasStockDetails 
                                    ? po_form_details.stock_detail.find(detail => detail.item_code === item.item_code) || {} 
                                    : {};
                                return `
                                    <tr>
                                        <td>${item.item_name}</td>
                                        <td>${frappe.format(item.qty, { fieldtype: "Float" })}</td>
                                        <td>${frappe.format(item.rate, { fieldtype: "Currency" })}</td>
                                        <td>${frappe.format(item.available_qty_in_target, { fieldtype: "Float" })}</td>
                                        <td>${frappe.format(item.total_available_stock, { fieldtype: "Float" })}</td>
                                        ${hasStockDetails ? `<td>${frappe.format(stockDetail.demand, { fieldtype: "Float" }) || 0}</td><td>${frappe.format(stockDetail.additional, { fieldtype: "Float" }) || 0}</td>` : ""}
                                    </tr>
                                `;
                            }).join("")}
                        </tbody>
                    </table>
                </div>`;

            if (po_form_details){
                po_form_details['total_stock'] = itemsWithStock.reduce((sum, item) => sum + (item.total_available_stock || 0), 0);
                // Fetch PO Form Details And Showcase in Purchase Order Details Dailog
                html += createPoDetailsHTML(po_form_details);
            }
    
            var d = new frappe.ui.Dialog({
                title: __("Purchase Order Details"),
                fields: [
                    {
                        fieldtype: "HTML",
                        fieldname: "po_details",
                        options: html
                    }
                ],
                size: 'extra-large',
                // primary_action_label: __(""),
                // primary_action: () => {
                //     d.hide();
                // },
                secondary_action_label: __("Cancel"),
                secondary_action: () => {
                    d.hide();
                }
            });
    
            d.show();
        });


        frm.add_custom_button(("Details New"), async () => {
            try {
                // Fetch document details via Frappe backend
                let response = await new Promise((resolve, reject) => {
                    frappe.call({
                        method: "mantra_dev.backend_code.detail_popup.fetch_document_details",
                        args: {
                            doctype: "Purchase Order",
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
                    size: 'extra-large',
                    primary_action_label: __("Close"),
                    primary_action: () => d.hide()
                });

                d.show();
            } catch (error) {
                console.error(error);
                frappe.msgprint(__("Failed to fetch purchase order details"));
            }
        
    
        });





        frm.add_custom_button(
            __("Rate Comparison"),
            function () {
                // Collect all item codes from the child table, ensuring valid values
                let item_codes = frm.doc.items.map(item => item.item_code).filter(Boolean);

                // Construct the report URL
                let report_url = "/app/query-report/Purchase Insight Report";

                if (item_codes.length > 0) {
                    // Convert the item list to a format recognized by multi-select filters
                    let item_filter = JSON.stringify(item_codes); 
                    report_url += "?item=" + encodeURIComponent(item_filter);
                }

                // Open the report in a new tab with the applied filters
                window.open(frappe.urllib.get_full_url(report_url), "_blank");
            },
            __('Utility') // Placing under Utility
        );

        if(frm.doc.docstatus !== 2){

            frm.add_custom_button(__('Calculate Project Qty'), function() {
    
                frappe.call({
                    method: "mantra_dev.backend_code.project.project.get_sales_order_items",
                    args: {
                        purchase_order: frm.doc.name
                    },
                    callback: function(response) {
                        if (response.message && response.message.length === 2) {
                            let aggregated_items = response.message[0]; 
                            let warehouse_list = response.message[1];
                            if (aggregated_items.length > 0) {
                                frappe.route_options = {
                                    data: JSON.stringify(aggregated_items),  
                                    warehouse: JSON.stringify(warehouse_list)  
                                }   
                            frappe.open_in_new_tab = true;
                            frappe.set_route('query-report', 'BOM Stock Calculated with Valuation rate');
                        }}  
                }
                });
            }, __('Utility'));


            frm.add_custom_button(__('Add PO Form Approval'), function () {
                frappe.db.get_value(
                    "PO Form Approval",
                    { purchase_order : frm.doc.name, docstatus: ['<', 2]},
                    "name",
                    (r) => {
                        frappe.open_in_new_tab = true;
                        if(r?.name){
                            frappe.set_route("Form","PO Form Approval",r.name)
                        }
                        else{
                            let po_form = frappe.model.get_new_doc("PO Form Approval");
                            frappe.route_options = {
                                purchase_order: frm.doc.name
                            };
                            frappe.set_route("Form", "PO Form Approval", po_form.name);                        
                        }
                })
            },
            __("Utility"));
        }
    },    
    before_save: function (frm) {
        frm.doc.items.forEach((item) => {
            if (item.item_code) {
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Item",
                        fieldname: ["custom_purchase_item_name", "item_name"],
                        filters: {
                            name: item.item_code
                        },
                    },
                    callback: function (r) {
                        var po_code = r.message.custom_purchase_item_name;
                        // Set the sales person field in the Lead form
                        if(item.custom_item_description== undefined || item.custom_item_description==""){
                            if (po_code) {
                                item.custom_item_description = po_code
                            }
                            else {
                                item.custom_item_description = r.message.item_name
                            }
                        }
                    },
                });

            }
            // frm.save()
        });


        // if(!frm.doc.custom_expense_grouping){
        //     frappe.throw("Please Select Department and Expense Grouping if it is not present Then tell Admin to Create Expense Grouping for that Department.")
        // }
        // if(!frm.doc.custom_department){
        //     frappe.throw("Please Select the Department")
        // }
    },
    
    after_save(frm){


        // let approvers = [
        //     frm.doc.custom_approver_1,
        //     frm.doc.custom_approver_2,
        //     frm.doc.custom_approver_3,
        //     frm.doc.custom_approver_4,
        //     frm.doc.custom_approver_5
        // ].filter(approver => approver)
        // console.log("----->",approvers);
        
        // if(approvers){

        //     frappe.call({
        //         method: "mantra_dev.backend_code.api.share_document",
        //         args: {
        //             doctype: "Purchase Order",
        //             name: frm.doc.name,
        //             users: approvers,
        //             read: 1,
        //             write: 1,
        //             share: 0,
        //             everyone: 0
        //         },
        //         callback(r) {
        //             if(r.message) {
        //                 console.log(r.message);
        //                 frm.reload_doc()
        //                 // document is shared with user
        //             }
        //         }
        //     })
        // }
    },




    custom_department(frm){
        // frm.set_value("custom_expense_grouping","")
        // frm.fields_dict["custom_expense_grouping"].get_query = function () {
        //     let selected_department = frm.doc.custom_department;
        //     if (!selected_department) {
        //         return {};
        //     }
        //     return {
        //         filters: {
        //             name: ["in", get_selected_values(selected_department)]
        //         }
        //     };
        // };
    },
    validate(frm){
        // frappe.call({
        //     method: "mantra_dev.backend_code.api.get_verification_users",
        //     args: {
        //         expense_grouping_master: frm.doc.custom_expense_grouping,
        //         department: frm.doc.custom_department
        //     },
        //     callback: function(r) {
        //         if (r.message) {
        //         // Fill approver fields only if they are empty
        //         if (!frm.doc.custom_approver_1 || ""){
        //             frm.set_value("custom_approver_1", r.message[0][0] || "");
        //             frm.set_value("custom_approver_2", r.message[0][1] || "");
        //             frm.set_value("custom_approver_3", r.message[0][2] || "");
        //             frm.set_value("custom_approver_4", r.message[0][3] || "");
        //             frm.set_value("custom_approver_5", r.message[0][4] || "");
        //         } 
        //         // Find the last non-empty approver from the document fields
        //         let approvers = [
        //             frm.doc.custom_approver_1,
        //             frm.doc.custom_approver_2,
        //             frm.doc.custom_approver_3,
        //             frm.doc.custom_approver_4,
        //             frm.doc.custom_approver_5
        //         ];

        //         let last_approver = "";
        //         for (let i = approvers.length - 1; i >= 0; i--) { // Start from custom_approver_5 and go backwards
        //             if (approvers[i]) {
        //                 last_approver = approvers[i];
        //                 break;
        //             }
        //         }

        //         frm.set_value("custom_final_approver", last_approver);
        //         }else{
        //             // Find the last non-empty approver from the document fields
        //         let approvers = [
        //             frm.doc.custom_approver_1,
        //             frm.doc.custom_approver_2,
        //             frm.doc.custom_approver_3,
        //             frm.doc.custom_approver_4,
        //             frm.doc.custom_approver_5
        //         ];

        //         if(approvers=[] || !approvers){
        //             frappe.throw("There is no approver in verification flow and you have also not selected any approver.")
        //             return
        //         }

        //         let last_approver = "";
        //         for (let i = approvers.length - 1; i >= 0; i--) { // Start from custom_approver_5 and go backwards
        //             if (approvers[i]) {
        //                 last_approver = approvers[i];
        //                 break;
        //             }
        //         }

        //         frm.set_value("custom_final_approver", last_approver);

        //         }
        //     }
        // });
    },
});

// function get_selected_values(department) {
//     let selected_values = [];
//     frappe.call({
//         method: "frappe.client.get_list",
//         async: false,
//         args: {
//             doctype: "Expense Verification Flow",
//             filters: { select_department: department }, // Filter by selected department
//             fields: ["select_expense_grouping"]
//         },
//         callback: function (r) {
//             if (r.message) {
//                 selected_values = r.message.map(row => row.select_expense_grouping);
//             }
//         }
//     });
//     return selected_values;
// }


function createPoDetailsHTML(po_form_details){
    html = `
        <style>
            .po-form-approval td div, .item-stock td div {
                text-align: left !important;
            }
            .po-form-approval td {
                width: 14.29%;
            }
        </style>
        <h4>PO Form Approval Details:</h4>
        <table class="table table-bordered po-form-approval">
            <tbody>
                <tr>
                    <td>Project Code:</td>
                    <td colspan="2">${po_form_details.project || ''}</td>
                    <td>Project Name:</td>
                    <td colspan="3">${po_form_details.project_name || ''}</td>
                </tr>
                <tr>
                    <td>Sales Order No:</td>
                    <td colspan="2">${po_form_details.sales_order || ''}</td>
                    <td>Customer PO No:</td>
                    <td colspan="3">${po_form_details.po_no || ''}</td>
                </tr>
                <tr>
                    <td>Customer Code:</td>
                    <td colspan="2">${po_form_details.customer || ''}</td>
                    <td>Customer Name:</td>
                    <td colspan="3">${po_form_details.customer_name || ''}</td>
                </tr>
                <tr>
                    <td>Business Unit Name:</td>
                    <td colspan="2">${po_form_details.business_unit_name || ''}</td>
                    <td>Business Unit Email:</td>
                    <td colspan="3">${po_form_details.business_unit_email || ''}</td>
                </tr>
                <tr>
                    <td>Purpose:</td>
                    <td colspan="6">${po_form_details.purpose || ''}</td>
                </tr>
                <tr>
                    <td>Cost Center/Profit Center:</td>
                    <td colspan="6">${po_form_details.cost_center || ''}</td>
                </tr>
                <tr>
                    <td>Requester:</td>
                    <td colspan="2">${po_form_details.requester || ''}</td>
                    <td>Approved By:</td>
                    <td colspan="3">${po_form_details.approved_by || ''}</td>
                </tr>
                <tr>
                    <td>Material Request:</td>
                    <td colspan="2">${po_form_details.material_request || ''}</td>
                    <td>Request By:</td>
                    <td colspan="3">${po_form_details.request_by || ''}</td>
                </tr>
                <tr>
                    <td>Approval Link:</td>
                    <td colspan="6">
                        ${po_form_details.approval_link ? `
                        <button style="padding: 5px 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;" onclick="window.open('${po_form_details.approval_link}', '_blank')">
                        View Approval </button>` : ""}
                    </td>
                </tr>
                <tr>
                    <td>Overall Profit in case if Project:</td>
                    <td colspan="6">${frappe.format(po_form_details.overall_profit_in_case_if_project, { fieldtype: "Currency" }) || ''}</td>
                </tr>
                <tr>
                    <td>Last Lowest Price:</td>
                    <td colspan="6">${frappe.format(po_form_details.last_lowest_price, { fieldtype: "Currency" }) || ''}</td>
                </tr>
                <tr>
                    <td>Final Supplier Quotation Link:</td>
                    <td colspan="6">
                        ${po_form_details.final_supplier_quotation_link ? `
                        <button style="padding: 5px 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;" onclick="window.open('${po_form_details.final_supplier_quotation_link}', '_blank')">
                        View Quotation </button>` : ""}
                    </td>
                </tr>
                <tr>
                    <td>NDA:</td>
                    <td colspan="6">
                        ${po_form_details.nda ? `
                        <button style="padding: 5px 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;" onclick="window.open('${po_form_details.nda}', '_blank')" >
                        NDA </button>` : ""}
                    </td>
                </tr>
                <tr>
                    <td>Comments:</td>
                    <td colspan="6">${po_form_details.comment || ''}</td>
                </tr>`

    if (po_form_details.stock_detail.length > 0){
        html += `<tr>
            <td colspan="7" style="text-align: center;"><h3 style="margin-bottom: 0px !important;">Stock Detail</h3></td>
        </tr>
        <tr>
            <td>Item Code</td>
            <td>Item Name</td>
            <td>Qty</td>
            <td>Target Warehouse Qty</td>
            <td>Current Stock</td>
            <td>Demand</td>
            <td>Additional</td>
        </tr>`

        for (let item of po_form_details.stock_detail) {
            html += `
                <tr>
                    <td>${item.item_code}</td>
                    <td>${item.item_name}</td>
                    <td>${frappe.format(item.qty, { fieldtype: "Float" })}</td>
                    <td>${frappe.format(item.target_warehouse_qty, { fieldtype: "Float" })}</td>
                    <td>${frappe.format(item.current_stock, { fieldtype: "Float" })}</td>
                    <td>${frappe.format(item.demand, { fieldtype: "Float" }) || 0}</td>
                    <td>${frappe.format(item.additional, { fieldtype: "Float" }) || 0}</td>
                </tr>`;
        }
    }
    
    if (po_form_details.price_comparison.length > 0) {
        html += `<tr>
            <td colspan="7" style="text-align: center;">
                <h3 style="margin-bottom: 0px !important;">Price Comparison</h3>
            </td>
        </tr>`;
    
        // Slice the array to ensure a max of 6 entries
        let priceComparisonData = po_form_details.price_comparison.slice(0, 6);
    
        let tableHTML = `<tr><td></td>`;
    
        for (let i = 0; i < priceComparisonData.length; i++) {
            tableHTML += `<td>L${i + 1}</td>`;
        }
    
        tableHTML += `</tr>`;
    
        let fields_dict = {
            'supplier': 'Supplier Name',
            'quote_price_to_the_customer': 'Quote Price to the Customer',
            'total_purchase_price': 'Total Purchase Price',
            'supplier_quoted_price': 'Supplier Quoted Price',
            'nagotiated': 'Negotiated',
            'warranty_foc_spares': 'Warranty / FOC Spares (%)',
            'lead_time': 'Lead Time',
            'freight': 'Freight',
            'rate_contract': 'Rate Contract',
            'compliance__certificates_in_case_of_import': 'Compliance / Certificates (In case of IMPORT)',
            'payment_terms': 'Payment Terms',
            'incoterms_shipping_terms': 'Incoterms/ Shipping Terms',
        };
    
        let currency_fields = [
            'quote_price_to_the_customer', 
            'total_purchase_price', 
            'supplier_quoted_price', 
            'nagotiated', 
            'freight', 
            'rate_contract'
        ];
    
        for (let key in fields_dict) {
            tableHTML += `<tr>
                <td><b>${fields_dict[key]}</b></td>`;
    
            priceComparisonData.forEach(row => {
                let value = row[key] || '';
    
                if (currency_fields.includes(key) && value !== '') {
                    value = frappe.format(value, { fieldtype: "Currency" });
                }
    
                if (key == 'compliance__certificates_in_case_of_import') {
                    if (value) {
                        value = `<button style="padding: 5px 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;" onclick="window.open('${value}', '_blank')">
                            View Certificate</button>`;
                    } else {
                        value = '';
                    }
                }
    
                tableHTML += `<td style="word-wrap: break-word; max-width: 200px;" >${value}</td>`;
            });
    
            tableHTML += `</tr>`;
        }
    
        html += tableHTML;
    }
    

    html += `
            </tbody>
        </table>
    `;

    return html
}