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
    }
});