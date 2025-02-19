frappe.ui.form.on("Purchase Order", {
    onload: function (frm) {
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
                console.log("View Hide");
                frm.remove_custom_button("Update Items");
            }, 0);
        }
    },
    refresh: function (frm) {
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
    
            // Construct HTML content
            let html = `
                <div>
                    <h4>${po.name}</h4>
                    <p><strong>Supplier Name:</strong> ${po.supplier_name}</p>
                    <p><strong>Status:</strong> ${po.status}</p>
                    <p><strong>Grand Total:</strong> ${po.grand_total}</p>
                    <h5>Items:</h5>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Item Name</th>
                                <th>Qty</th>
                                <th>Rate</th>
                                <th>Target Warehouse Qty</th>
                                <th>Total Qty</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${itemsWithStock.map(item => `
                                <tr>
                                    <td>${item.item_name}</td>
                                    <td>${item.qty}</td>
                                    <td>${item.rate}</td>
                                    <td>${item.available_qty_in_target}</td>
                                    <td>${item.total_available_stock}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>`;
    
            var d = new frappe.ui.Dialog({
                title: __("Purchase Order Details"),
                fields: [
                    {
                        fieldtype: "HTML",
                        fieldname: "po_details",
                        options: html
                    }
                ],
                primary_action_label: __("Process"),
                primary_action: () => {
                    d.hide();
                },
                secondary_action_label: __("Cancel"),
                secondary_action: () => {
                    d.hide();
                }
            });
    
            d.show();
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


        if(!frm.doc.custom_expense_grouping){
            frappe.throw("Please Select Department and Expense Grouping if it is not present Then tell Admin to Create Expense Grouping for that Department.")
        }
        if(!frm.doc.custom_department){
            frappe.throw("Please Select the Department")
        }
    },
    
    after_save(frm){


        let approvers = [
            frm.doc.custom_approver_1,
            frm.doc.custom_approver_2,
            frm.doc.custom_approver_3,
            frm.doc.custom_approver_4,
            frm.doc.custom_approver_5
        ].filter(approver => approver)
        console.log("----->",approvers);
        
        if(approvers){

            frappe.call({
                method: "mantra_dev.backend_code.api.share_document",
                args: {
                    doctype: "Purchase Order",
                    name: frm.doc.name,
                    users: approvers,
                    read: 1,
                    write: 1,
                    share: 0,
                    everyone: 0
                },
                callback(r) {
                    if(r.message) {
                        console.log(r.message);
                        frm.reload_doc()
                        // document is shared with user
                    }
                }
            })
        }
    },




    custom_department(frm){
        frm.set_value("custom_expense_grouping","")
        frm.fields_dict["custom_expense_grouping"].get_query = function () {
            let selected_department = frm.doc.custom_department;
            if (!selected_department) {
                return {};
            }
            return {
                filters: {
                    name: ["in", get_selected_values(selected_department)]
                }
            };
        };
    },
    validate(frm){
        frappe.call({
            method: "mantra_dev.backend_code.api.get_verification_users",
            args: {
                expense_grouping_master: frm.doc.custom_expense_grouping,
                department: frm.doc.custom_department
            },
            callback: function(r) {
                if (r.message) {
                // Fill approver fields only if they are empty
                if (!frm.doc.custom_approver_1 || ""){
                    frm.set_value("custom_approver_1", r.message[0][0] || "");
                    frm.set_value("custom_approver_2", r.message[0][1] || "");
                    frm.set_value("custom_approver_3", r.message[0][2] || "");
                    frm.set_value("custom_approver_4", r.message[0][3] || "");
                    frm.set_value("custom_approver_5", r.message[0][4] || "");
                } 
                // Find the last non-empty approver from the document fields
                let approvers = [
                    frm.doc.custom_approver_1,
                    frm.doc.custom_approver_2,
                    frm.doc.custom_approver_3,
                    frm.doc.custom_approver_4,
                    frm.doc.custom_approver_5
                ];

                let last_approver = "";
                for (let i = approvers.length - 1; i >= 0; i--) { // Start from custom_approver_5 and go backwards
                    if (approvers[i]) {
                        last_approver = approvers[i];
                        break;
                    }
                }

                frm.set_value("custom_final_approver", last_approver);
                }else{
                    // Find the last non-empty approver from the document fields
                let approvers = [
                    frm.doc.custom_approver_1,
                    frm.doc.custom_approver_2,
                    frm.doc.custom_approver_3,
                    frm.doc.custom_approver_4,
                    frm.doc.custom_approver_5
                ];

                if(approvers=[] || !approvers){
                    frappe.throw("There is no approver in verification flow and you have also not selected any approver.")
                    return
                }

                let last_approver = "";
                for (let i = approvers.length - 1; i >= 0; i--) { // Start from custom_approver_5 and go backwards
                    if (approvers[i]) {
                        last_approver = approvers[i];
                        break;
                    }
                }

                frm.set_value("custom_final_approver", last_approver);

                }
            }
        });
    },
});

function get_selected_values(department) {
    let selected_values = [];
    frappe.call({
        method: "frappe.client.get_list",
        async: false,
        args: {
            doctype: "Expense Verification Flow",
            filters: { select_department: department }, // Filter by selected department
            fields: ["select_expense_grouping"]
        },
        callback: function (r) {
            if (r.message) {
                selected_values = r.message.map(row => row.select_expense_grouping);
            }
        }
    });
    return selected_values;
}