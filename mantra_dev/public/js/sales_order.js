frappe.ui.form.on('Sales Order', {
    onload: function (frm) {
        setTimeout(() => {
            frm.set_query('customer', () => {
                return {
                    filters: {
                        workflow_state: 'Approved'
                    }
                };
            });
        }, 1000); // 1000 milliseconds = 1 second   
        frm.set_query('set_warehouse', () => {
            return {
                filters: {
                    custom_is_sales_warehouse: 1
                }
            };
        });
        if (frappe.user_roles.includes("System Manager") == false) {
            setTimeout(() => {
                console.log("View Hide");
                frm.remove_custom_button("Update Items");
            }, 0);
        }
    },
    before_save(frm){
        frm.doc.items.forEach((item) => {
            if(item.custom_is_service_item==1){
                item.delivered_qty=item.qty
            }
            if (item.item_code) {
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Item",
                        fieldname: ["custom_sales_item_name", "item_name"],
                        filters: {
                            name: item.item_code
                        },
                    },
                    callback: function (r) {
                        var po_code = r.message.custom_sales_item_name;
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
        })
        refresh_field("items")
        
    },
    
    before_submit: function (frm) {
        var items = frm.doc.items.length
        var item_code = []
        frm.doc.items.forEach((item) => {
            if (item.item_code) {
                item_code.push(item.item_code)
            }
        })
        console.log(item_code)
        console.log(items)
        if (items != item_code.length) {
            frappe.throw("Please enter vaild Item Code")
            // validate:false
        }
        if (frm.doc.total == 0) {
            frm.set_value("per_billed", 100)
        }
        
    },
    refresh: function (frm) {
        // Check if the document is in draft (docstatus 0) and not new
        if (frm.doc.docstatus == 0 && !frm.is_new()) {
            // Check if the user does not have the "Item Requester" role
            // if (!frappe.user_roles.includes("Item Requester")) {
                frm.add_custom_button(__('Item Code Request'), function () {
                    // Call custom function when button is clicked
                    openQuickEntryForm(frm);
                });
            // }
        }

        // Check if the document is submitted (docstatus 1)
        if (frm.doc.docstatus === 1) {
            // Additional conditions for submitted documents
            if (frm.doc.status !== "Closed" && flt(frm.doc.per_delivered, 2) < 100 && flt(frm.doc.per_billed, 2) < 100) {
                frm.add_custom_button(__("Update Items"), () => {
                    erpnext.utils.update_child_items({
                        frm: frm,
                        child_docname: "items",
                        child_doctype: "Sales Order Detail",
                        cannot_add_row: false,
                        has_reserved_stock: frm.doc.__onload && frm.doc.__onload.has_reserved_stock,
                    });
                });

                // Check if the default currency is USD and additional conditions
                frappe.db.get_single_value('Custom Settings', 'role_allowed_to_reserve_stock').then(value => {
                    console.log('Default Currency:', value);
                    if (frappe.user.has_role(value)) {
                        if (frm.doc.__onload && frm.doc.__onload.has_unreserved_stock && flt(frm.doc.per_picked) === 0) {
                            frm.add_custom_button(
                                __("Reserve"),
                                () => frm.events.create_stock_reservation_entries(frm),
                                __("Stock Reservation")
                            );
                        }
                    }
                })

                // Show Unreserve button if there is un-delivered reserved stock
                if (frm.doc.__onload && frm.doc.__onload.has_reserved_stock) {
                    frm.add_custom_button(
                        __("Unreserve"),
                        () => frm.events.cancel_stock_reservation_entries(frm),
                        __("Stock Reservation")
                    );
                }

                // Show Reserved Stock button if any item has reserved stock quantity
                frm.doc.items.forEach((item) => {
                    if (flt(item.stock_reserved_qty) > 0) {
                        frm.add_custom_button(
                            __("Reserved Stock"),
                            () => frm.events.show_reserved_stock(frm),
                            __("Stock Reservation")
                        );
                        return;  // Exit the loop once the button is added
                    }
                });
            }

            // Additional checks for internal customer orders
            if (frm.doc.is_internal_customer) {
                frm.events.get_items_from_internal_purchase_order(frm);
            }

            // Hide `Reserve Stock` field if not in draft status
            if (frm.doc.docstatus === 0) {
                frappe.call({
                    method: "erpnext.selling.doctype.sales_order.sales_order.get_stock_reservation_status",
                    callback: function (r) {
                        if (!r.message) {
                            frm.set_value("reserve_stock", 0);
                            frm.set_df_property("reserve_stock", "read_only", 1);
                            frm.set_df_property("reserve_stock", "hidden", 1);
                            frm.fields_dict.items.grid.update_docfield_property("reserve_stock", "hidden", 1);
                            frm.fields_dict.items.grid.update_docfield_property("reserve_stock", "default", 0);
                            frm.fields_dict.items.grid.update_docfield_property("reserve_stock", "read_only", 1);
                        }
                    },
                });
            }

            // Remove `Reserve Stock` field description for submitted or cancelled Sales Orders
            if (frm.doc.docstatus > 0) {
                frm.set_df_property("reserve_stock", "description", null);
            }
        }
    },
    create_stock_reservation_entries(frm) {
        
        const dialog = new frappe.ui.Dialog({
            title: __("Stock Reservation"),
            size: "extra-large",
            fields: [
                {
                    fieldname: "set_warehouse",
                    fieldtype: "Link",
                    label: __("Set Warehouse"),
                    options: "Warehouse",
                    default: frm.doc.set_warehouse,
                    get_query: () => {
                        return {
                            filters: [["Warehouse", "is_group", "!=", 1]],
                        };
                    },
                    onchange: () => {
                        if (dialog.get_value("set_warehouse")) {
                            dialog.fields_dict.items.df.data.forEach((row) => {
                                row.warehouse = dialog.get_value("set_warehouse");
                            });
                            dialog.fields_dict.items.grid.refresh();
                        }
                    },
                },
                { fieldtype: "Column Break" },
                {
                    fieldname: "add_item",
                    fieldtype: "Link",
                    label: __("Add Item"),
                    options: "Sales Order Item",
                    get_query: () => {
                        return {
                            query: "erpnext.controllers.queries.get_filtered_child_rows",
                            filters: {
                                parenttype: frm.doc.doctype,
                                parent: frm.doc.name,
                                reserve_stock: 1,
                            },
                        };
                    },
                    onchange: () => {
                        var unreserved_qty=0
                        let sales_order_item = dialog.get_value("add_item");
                        if (sales_order_item){
                            frappe.call({
                                method: "mantra_dev.backend_code.api.get_pending_qty",
                                args: {
                                    lineid: sales_order_item,
                                    so_id:frm.doc.name
                                },
                                callback: function(response) {
                                    alert(response.message.pending_qty)
                                    if(response.message.pending_qty !== 'Error'){
                                        unreserved_qty=response.message.pending_qty
                                        if (sales_order_item) {
                                            frm.doc.items.forEach((item) => {
                                                    dialog.fields_dict.items.df.data.push({
                                                        __checked: 1,
                                                        sales_order_item: item.name,
                                                        item_code: item.item_code,
                                                        total_qty: item.qty,
                                                        warehouse: dialog.get_value("set_warehouse") || item.warehouse,
                                                        pending_qty: unreserved_qty,
                                                    });
                                                    dialog.fields_dict.items.grid.refresh();
                                                    dialog.set_value("add_item", undefined);
                                                // }
                                            });
                                        }
                                    }
                                },
                            });
                        }
                    },
                },

                { fieldtype: "Section Break" },
                {
                    fieldname: "items",
                    fieldtype: "Table",
                    label: __("Items to Reserve"),
                    allow_bulk_edit: false,
                    cannot_add_rows: true,
                    cannot_delete_rows: false,
                    data: [],
                    description: "if the checkbox is checked then only stock will be reserved",
                    fields: [
                        {
                            fieldname: "sales_order_item",
                            fieldtype: "Link",
                            label: __("Sales Order Item"),
                            options: "Sales Order Item",
                            reqd: 1,
                            in_list_view: 1,
                            get_query: () => {
                                return {
                                    query: "erpnext.controllers.queries.get_filtered_child_rows",
                                    filters: {
                                        parenttype: frm.doc.doctype,
                                        parent: frm.doc.name,
                                        reserve_stock: 1,
                                    },
                                };
                            },
                            onchange: (event) => {
                                if (event) {
                                    // alert("alert")
                                    let name = $(event.currentTarget).closest(".grid-row").attr("data-name");
                                    let item_row =
                                        dialog.fields_dict.items.grid.grid_rows_by_docname[name].doc;

                                    frm.doc.items.forEach((item) => {
                                        if (item.name === item_row.sales_order_item) {
                                            // alert("iff")
                                            item_row.item_code = item.item_code;
                                        }
                                        else {
                                            // alert("else")
                                        }
                                    });
                                    dialog.fields_dict.items.grid.refresh();
                                }
                            },
                        },
                        {
                            fieldname: "item_code",
                            fieldtype: "Link",
                            label: __("Item Code"),
                            options: "Item",
                            reqd: 1,
                            read_only: 1,
                            in_list_view: 1,
                            fetch_from: "sales_order_item.item_code"
                        },

                        {
                            fieldname: "warehouse",
                            fieldtype: "Link",
                            label: __("Warehouse"),
                            options: "Warehouse",
                            reqd: 1,
                            in_list_view: 0,
                            get_query: () => {
                                return {
                                    filters: [["Warehouse", "is_group", "!=", 1]],
                                };
                            },
                        },
                        {
                            fieldname: "pending_qty",
                            fieldtype: "Float",
                            label: __("Pending Qty"),
                            reqd: 1,
                            read_only:1,
                            in_list_view: 1,

                        },
                        {
                            fieldname: "qty_to_reserve",
                            fieldtype: "Float",
                            label: __("Qty"),
                            reqd: 1,
                            in_list_view: 1,
                            onchange: (event) => {
                                // console.log(event)
                                if (event) {
                                    let name = $(event.currentTarget).closest(".grid-row").attr("data-name");
                                    let item_row = dialog.fields_dict.items.grid.grid_rows_by_docname[name].doc;
                                    let sales_order_item = dialog.get_value("items");

                                    for (var i1 = 1; i1 <= sales_order_item.length; i1++) {
                                        let integerValue = Math.trunc(i1);
                                        // console.log(sales_order_item[i1 - 1]["item_code"]);
                                        let i = item_row.pending_qty - item_row.qty_to_reserve;
                                        // console.log(i1);

                                        if (item_row.sales_order_item == sales_order_item[i1 - 1]["sales_order_item"]) {
                                            console.log("Item code matched", i1, item_row.idx);
                                            if (i1 > item_row.idx) { // This condition needs 
                                                sales_order_item[i1 - 1]["pending_qty"] = i;
                                                sales_order_item[i1 - 1]["qty_to_reserve"] = 0;
                                            }
                                        }
                                    }
                                }
                                dialog.fields_dict.items.grid.refresh();

                            },
                        },
                        {
                            fieldname: "total_qty",
                            fieldtype: "Float",
                            label: __("Total Qty"),
                            reqd: 1,
                            in_list_view: 0,
                        },
                        {
                            fieldname: "delivery_date",
                            fieldtype: "Date",
                            label: __("Delivery Date"),
                            reqd: 1,
                            in_list_view: 1,
                            default: frappe.datetime.get_today() // Use frappe.datetime.get_today() to get today's date
                        },
                    ],
                },
                {
                    fieldname: "add_row_and_delete",
                    fieldtype: "Section Break",
                },

            ],
            primary_action_label: __("Reserve Stock"),
            primary_action: () => {
                var data = { items: dialog.fields_dict.items.grid.get_selected_children() };

                if (data.items && data.items.length > 0) {
                    // for(var a=0;a<data.items.length;a++){
                    //     console.log(data.items[a])
                    // }
                    console.log(data.items)
                    frappe.call({
                        doc: frm.doc,
                        method: "create_stock_reservation_entries",
                        args: {
                            items_details: data.items,
                            notify: true,
                        },
                        freeze: true,
                        freeze_message: __("Reserving Stock..."),
                        callback: (r) => {
                            frm.doc.__onload.has_unreserved_stock = false;
                            frm.reload_doc();
                        },
                    });

                    dialog.hide();
                } else {
                    frappe.msgprint(__("Please select items to reserve."));
                }
            },
        });

        frm.doc.items.forEach((item) => {
            if (item.reserve_stock) {
                setTimeout(() => {
                    frappe.call({
                        method: "mantra_dev.backend_code.api.get_pending_qty",
                        args: {
                            lineid: item.name,
                            so_id:frm.doc.name
                        },
                        callback: function(response) {
                            // alert(response.message.pending_qty)
                            if(response.message.pending_qty !== 'Error'){
                                unreserved_qty=response.message.pending_qty
                                // if (sales_order_item) {
                                    frm.doc.items.forEach((item) => {
                                            dialog.fields_dict.items.df.data.push({
                                                __checked: 1,
                                                sales_order_item: item.name,
                                                item_code: item.item_code,
                                                total_qty: item.qty,
                                                warehouse: dialog.get_value("set_warehouse") || item.warehouse,
                                                pending_qty: unreserved_qty,
                                            });
                                            dialog.fields_dict.items.grid.refresh();
                                            // dialog.set_value("add_item", undefined);
                                        // }
                                    });
                                // }
                            }
                        },
                    });
                }, 0);
            }
        });

        dialog.fields_dict.items.grid.refresh();
        dialog.show();

    },
});
// Custom function to open the quick entry form
function openQuickEntryForm(frm) {
    var custom_item_description = [];
    var fields = []
    $.each(frm.doc.items || [], function (i, d) {
        if (d.item_code == undefined && d.custom_item_code_request_generate == 0 || d.item_code == "") {
            custom_item_description.push(d.custom_item_description);
        }
    });
    for (var i = 0; i < custom_item_description.length; i++) {
        fields.push({
            fieldname: custom_item_description[i],
            label: __(custom_item_description[i]),
            fieldtype: 'Check',
            default: 0
        })
    }
    var dialog = new frappe.ui.Dialog({
        title: 'Item Code Request',
        fields: fields,
        primary_action: function () {
            var values = dialog.get_values();
            var keysList = objectToList(values, 'keys');
            var valuesList = objectToList(values, 'values');
            for (var i1 = 0; i1 < keysList.length; i1++) {
                // console.log(valuesList[i])
                if (valuesList[i1] == 1) {
                    var line = '';
                    var item_description = '';
                    $.each(frm.doc.items || [], function (i, d) {
                        // let d = locals[cdt][cdn];
                        console.log(d.custom_item_description, "fjgfumugfjj")
                        console.log(keysList[i1], "keylist")
                        if (d.item_code == undefined && d.custom_item_code_request_generate == 0 || d.item_code == "") {
                            if (d.custom_item_description == keysList[i1]) {
                                console.log(keysList[i1], "  Key list")
                                line = d.name;
                                item_description = d.custom_item_description;
                                frappe.call({
                                    method: "frappe.client.insert",
                                    args: {
                                        doc: {
                                            doctype: "Item Code Request",
                                            // Add your field values here
                                            "sales_order_id": frm.doc.name,
                                            "item_name": keysList[i1],
                                            "description": item_description,
                                            "requesting_date": frappe.datetime.now_datetime(),
                                            "line_id": line,
                                            "user_id": frappe.session.user,
                                            "doument_attachment": d.custom_document_attachment,
                                            "form_type": "Sales Order",
                                            "uom": d.uom
                                            // Add more fields as needed
                                        }
                                    },
                                    callback: function (response) {
                                        if (!response.exc) {
                                            // Success
                                            console.log(response)
                                            console.log("New record created successfully!");
                                            d.custom_item_code_request_generate = 1
                                            d.custom_item_request_id = response.message.name
                                            frm.set_value("custom_process_status", "Open")
                                            frm.set_value("custom_process_status", "In progress")

                                            // // cur_frm.refresh_field("items");
                                            // cur_frm.fields_dict['items'].grid.grid_rows_by_docname[d.name].doc.custom_item_code_request_generate = 1;
                                            // // Refresh the field
                                            // cur_frm.fields_dict['items'].grid.grid_rows_by_docname[d.name].refresh_field('custom_item_code_request_generate');

                                        } else {
                                            // Error
                                            console.log("Error occurred:", response.exc);
                                        }
                                    }
                                });
                            }
                        }
                    });

                    cur_frm.refresh_field("items");
                }
                frm.save()
                cur_frm.refresh_field("items");
            }
            dialog.hide();

        }

    });

    dialog.show();
}
function objectToList(obj, type) {
    if (type === 'keys') {
        return Object.keys(obj);
    } else if (type === 'values') {
        return Object.values(obj);
    } else {
        return null; // Handle invalid type
    }
}
frappe.ui.form.on('Sales Order Item', {
	qty(frm) {
        // delivered_qty
		// your code here
        frm.doc.items.forEach((item) => {
            if(item.custom_is_service_item==1){
                item.delivered_qty=item.qty
            }
            
            
        })
        refresh_field("items")
	},

})