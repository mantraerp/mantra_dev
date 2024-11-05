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