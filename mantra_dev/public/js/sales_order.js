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


erpnext.selling.SalesOrderController = class SalesOrderController extends erpnext.selling.SellingController {
	onload(doc, dt, dn) {
		super.onload(doc, dt, dn);
	}

	refresh(doc, dt, dn) {
		var me = this;
		super.refresh();
		let allow_delivery = false;

		if (doc.docstatus == 1) {
			if (this.frm.has_perm("submit")) {
				if (doc.status === "On Hold") {
					// un-hold
					this.frm.add_custom_button(
						__("Resume"),
						function () {
							me.frm.cscript.update_status("Resume", "Draft");
						},
						__("Status")
					);

					if (flt(doc.per_delivered, 2) < 100 || flt(doc.per_billed, 2) < 100) {
						// close
						this.frm.add_custom_button(__("Close"), () => this.close_sales_order(), __("Status"));
					}
				} else if (doc.status === "Closed") {
					// un-close
					this.frm.add_custom_button(
						__("Re-open"),
						function () {
							me.frm.cscript.update_status("Re-open", "Draft");
						},
						__("Status")
					);
				}
			}
			if (doc.status !== "Closed") {
				if (doc.status !== "On Hold") {
					allow_delivery =
						this.frm.doc.items.some(
							(item) => item.delivered_by_supplier === 0 && item.qty > flt(item.delivered_qty)
						) && !this.frm.doc.skip_delivery_note;

					if (this.frm.has_perm("submit")) {
						if (flt(doc.per_delivered, 2) < 100 || flt(doc.per_billed, 2) < 100) {
							// hold
							this.frm.add_custom_button(
								__("Hold"),
								() => this.hold_sales_order(),
								__("Status")
							);
							// close
							this.frm.add_custom_button(
								__("Close"),
								() => this.close_sales_order(),
								__("Status")
							);
						}
					}

					if (
						(!doc.__onload || !doc.__onload.has_reserved_stock) &&
						flt(doc.per_picked, 2) < 100 &&
						flt(doc.per_delivered, 2) < 100 &&
						frappe.model.can_create("Pick List")
					) {
						this.frm.add_custom_button(
							__("Pick List"),
							() => this.create_pick_list(),
							__("Create")
						);
					}

					const order_is_a_sale = ["Sales", "Shopping Cart"].indexOf(doc.order_type) !== -1;
					const order_is_maintenance = ["Maintenance"].indexOf(doc.order_type) !== -1;
					// order type has been customised then show all the action buttons
					const order_is_a_custom_sale =
						["Sales", "Shopping Cart", "Maintenance"].indexOf(doc.order_type) === -1;

					// delivery note
					if (
						flt(doc.per_delivered, 2) < 100 &&
						(order_is_a_sale || order_is_a_custom_sale) &&
						allow_delivery
					) {
						if (frappe.model.can_create("Delivery Note")) {
							this.frm.add_custom_button(
								__("Delivery Note"),
								() => this.make_delivery_note_based_on_delivery_date(true),
								__("Create")
							);
						}

						if (frappe.model.can_create("Work Order")) {
							this.frm.add_custom_button(
								__("Work Order"),
								() => this.make_work_order(),
								__("Create")
							);
						}
					}

					// sales invoice
					if (flt(doc.per_billed, 2) < 100 && frappe.model.can_create("Sales Invoice")) {
						this.frm.add_custom_button(
							__("Sales Invoice"),
							() => me.make_sales_invoice(),
							__("Create")
						);
					}

					// material request
					if (
						(!doc.order_type ||
							((order_is_a_sale || order_is_a_custom_sale) &&
								flt(doc.per_delivered, 2) < 100)) &&
						frappe.model.can_create("Material Request")
					) {
						this.frm.add_custom_button(
							__("Material Request"),
							() => this.make_material_request(),
							__("Create")
						);
						this.frm.add_custom_button(
							__("Request for Raw Materials"),
							() => this.make_raw_material_request(),
							__("Create")
						);
					}

					// Make Purchase Order
					if (!this.frm.doc.is_internal_customer && frappe.model.can_create("Purchase Order")) {
						this.frm.add_custom_button(
							__("Purchase Order"),
							() => this.make_purchase_order(),
							__("Create")
						);
					}

					// maintenance
					if (flt(doc.per_delivered, 2) < 100 && (order_is_maintenance || order_is_a_custom_sale)) {
						if (frappe.model.can_create("Maintenance Visit")) {
							this.frm.add_custom_button(
								__("Maintenance Visit"),
								() => this.make_maintenance_visit(),
								__("Create")
							);
						}
						if (frappe.model.can_create("Maintenance Schedule")) {
							this.frm.add_custom_button(
								__("Maintenance Schedule"),
								() => this.make_maintenance_schedule(),
								__("Create")
							);
						}
					}

					// project
					if (flt(doc.per_delivered, 2) < 100 && frappe.model.can_create("Project")) {
						this.frm.add_custom_button(__("Project"), () => this.make_project(), __("Create"));
					}

					if (
						doc.docstatus === 1 &&
						!doc.inter_company_order_reference &&
						frappe.model.can_create("Purchase Order")
					) {
						let me = this;
						let internal = me.frm.doc.is_internal_customer;
						if (internal) {
							let button_label =
								me.frm.doc.company === me.frm.doc.represents_company
									? "Internal Purchase Order"
									: "Inter Company Purchase Order";

							me.frm.add_custom_button(
								button_label,
								function () {
									me.make_inter_company_order();
								},
								__("Create")
							);
						}
					}
				}
				// payment request
				if (
					flt(doc.per_billed, precision("per_billed", doc)) <
					100 + frappe.boot.sysdefaults.over_billing_allowance
				) {
					this.frm.add_custom_button(
						__("Payment Request"),
						() => this.make_payment_request(),
						__("Create")
					);

					if (frappe.model.can_create("Payment Entry")) {
						this.frm.add_custom_button(
							__("Payment"),
							() => this.make_payment_entry(),
							__("Create")
						);
					}
				}
				this.frm.page.set_inner_btn_group_as_primary(__("Create"));
			}
		}

		if (this.frm.doc.docstatus === 0 && frappe.model.can_read("Quotation")) {
			this.frm.add_custom_button(
				__("Quotation"),
				function () {
					let d = erpnext.utils.map_current_doc({
						method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
						source_doctype: "Quotation",
						target: me.frm,
						setters: [
							{
								label: "Customer",
								fieldname: "party_name",
								fieldtype: "Link",
								options: "Customer",
								default: me.frm.doc.customer || undefined,
							},
						],
						get_query_filters: {
							company: me.frm.doc.company,
							docstatus: 1,
							status: ["!=", "Lost"],
						},
					});

					setTimeout(() => {
						d.$parent.append(`
							<span class='small text-muted'>
								${__("Note: Please create Sales Orders from individual Quotations to select from among Alternative Items.")}
							</span>
					`);
					}, 200);
				},
				__("Get Items From")
			);
		}

		this.order_type(doc);
	}

	create_pick_list() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.create_pick_list",
			frm: this.frm,
		});
	}

	make_work_order() {
		var me = this;
		me.frm.call({
			method: "erpnext.selling.doctype.sales_order.sales_order.get_work_order_items",
			args: {
				sales_order: this.frm.docname,
			},
			freeze: true,
			callback: function (r) {
				if (!r.message) {
					frappe.msgprint({
						title: __("Work Order not created"),
						message: __("No Items with Bill of Materials to Manufacture"),
						indicator: "orange",
					});
					return;
				} else {
					const fields = [
						{
							label: "Items",
							fieldtype: "Table",
							fieldname: "items",
							description: __("Select BOM and Qty for Production"),
							fields: [
								{
									fieldtype: "Read Only",
									fieldname: "item_code",
									label: __("Item Code"),
									in_list_view: 1,
								},
								{
									fieldtype: "Link",
									fieldname: "bom",
									options: "BOM",
									reqd: 1,
									label: __("Select BOM"),
									in_list_view: 1,
									get_query: function (doc) {
										return { filters: { item: doc.item_code } };
									},
								},
								{
									fieldtype: "Float",
									fieldname: "pending_qty",
									reqd: 1,
									label: __("Qty"),
									in_list_view: 1,
								},
								{
									fieldtype: "Data",
									fieldname: "sales_order_item",
									reqd: 1,
									label: __("Sales Order Item"),
									hidden: 1,
								},
							],
							data: r.message,
							get_data: () => {
								return r.message;
							},
						},
					];
					var d = new frappe.ui.Dialog({
						title: __("Select Items to Manufacture"),
						fields: fields,
						primary_action: function () {
							var data = { items: d.fields_dict.items.grid.get_selected_children() };
							if (!data) {
								frappe.throw(__("Please select items"));
							}
							me.frm.call({
								method: "make_work_orders",
								args: {
									items: data,
									company: me.frm.doc.company,
									sales_order: me.frm.docname,
									project: me.frm.project,
								},
								freeze: true,
								callback: function (r) {
									if (r.message) {
										frappe.msgprint({
											message: __("Work Orders Created: {0}", [
												r.message
													.map(function (d) {
														return repl(
															'<a href="/app/work-order/%(name)s">%(name)s</a>',
															{ name: d }
														);
													})
													.join(", "),
											]),
											indicator: "green",
										});
									}
									d.hide();
								},
							});
						},
						primary_action_label: __("Create"),
					});
					d.show();
				}
			},
		});
	}

	order_type() {
		this.toggle_delivery_date();
	}

	tc_name() {
		this.get_terms();
	}

	make_material_request() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_material_request",
			frm: this.frm,
		});
	}

	skip_delivery_note() {
		this.toggle_delivery_date();
	}

	toggle_delivery_date() {
		this.frm.fields_dict.items.grid.toggle_reqd(
			"delivery_date",
			this.frm.doc.order_type == "Sales" && !this.frm.doc.skip_delivery_note
		);
	}

	make_raw_material_request() {
		var me = this;
		this.frm.call({
			method: "erpnext.selling.doctype.sales_order.sales_order.get_work_order_items",
			args: {
				sales_order: this.frm.docname,
				for_raw_material_request: 1,
			},
			callback: function (r) {
				if (!r.message) {
					frappe.msgprint({
						message: __("No Items with Bill of Materials."),
						indicator: "orange",
					});
					return;
				} else {
					me.make_raw_material_request_dialog(r);
				}
			},
		});
	}

	make_raw_material_request_dialog(r) {
		var me = this;
		var fields = [
			{ fieldtype: "Check", fieldname: "include_exploded_items", label: __("Include Exploded Items") },
			{
				fieldtype: "Check",
				fieldname: "ignore_existing_ordered_qty",
				label: __("Ignore Existing Ordered Qty"),
			},
			{
				fieldtype: "Table",
				fieldname: "items",
				description: __("Select BOM, Qty and For Warehouse"),
				fields: [
					{
						fieldtype: "Read Only",
						fieldname: "item_code",
						label: __("Item Code"),
						in_list_view: 1,
					},
					{
						fieldtype: "Link",
						fieldname: "warehouse",
						options: "Warehouse",
						label: __("For Warehouse"),
						in_list_view: 1,
					},
					{
						fieldtype: "Link",
						fieldname: "bom",
						options: "BOM",
						reqd: 1,
						label: __("BOM"),
						in_list_view: 1,
						get_query: function (doc) {
							return { filters: { item: doc.item_code } };
						},
					},
					{
						fieldtype: "Float",
						fieldname: "required_qty",
						reqd: 1,
						label: __("Qty"),
						in_list_view: 1,
					},
				],
				data: r.message,
				get_data: function () {
					return r.message;
				},
			},
		];
		var d = new frappe.ui.Dialog({
			title: __("Items for Raw Material Request"),
			fields: fields,
			primary_action: function () {
				var data = d.get_values();
				me.frm.call({
					method: "erpnext.selling.doctype.sales_order.sales_order.make_raw_material_request",
					args: {
						items: data,
						company: me.frm.doc.company,
						sales_order: me.frm.docname,
						project: me.frm.project,
					},
					freeze: true,
					callback: function (r) {
						if (r.message.length < 2) {
							frappe.msgprint(
								__("Material Request {0} submitted.", [
									'<a href="/app/material-request/' +
										r.message.name +
										'">' +
										r.message.name +
										"</a>",
								])
							);
							
						}
						else{
						frappe.msgprint(
								__("Material Requests {0} and {1} submitted.", [
									'<a href="/app/material-request/' +
									r.message[0].name +
									'">' +
									r.message[0].name +
									"</a>",
									'<a href="/app/material-request/' +
									r.message[1].name +
									'">' +
									r.message[1].name +
									"</a>"
								])
							);
						}
						d.hide();
						me.frm.reload_doc();
					},
				});
			},
			primary_action_label: __("Create"),
		});
		d.show();
	}

	make_delivery_note_based_on_delivery_date(for_reserved_stock = false) {
		var me = this;

		var delivery_dates = this.frm.doc.items.map((i) => i.delivery_date);
		delivery_dates = [...new Set(delivery_dates)];

		var item_grid = this.frm.fields_dict["items"].grid;
		if (!item_grid.get_selected().length && delivery_dates.length > 1) {
			var dialog = new frappe.ui.Dialog({
				title: __("Select Items based on Delivery Date"),
				fields: [{ fieldtype: "HTML", fieldname: "dates_html" }],
			});

			var html = $(`
				<div style="border: 1px solid #d1d8dd">
					<div class="list-item list-item--head">
						<div class="list-item__content list-item__content--flex-2">
							${__("Delivery Date")}
						</div>
					</div>
					${delivery_dates
						.map(
							(date) => `
						<div class="list-item">
							<div class="list-item__content list-item__content--flex-2">
								<label>
								<input type="checkbox" data-date="${date}" checked="checked"/>
								${frappe.datetime.str_to_user(date)}
								</label>
							</div>
						</div>
					`
						)
						.join("")}
				</div>
			`);

			var wrapper = dialog.fields_dict.dates_html.$wrapper;
			wrapper.html(html);

			dialog.set_primary_action(__("Select"), function () {
				var dates = wrapper
					.find("input[type=checkbox]:checked")
					.map((i, el) => $(el).attr("data-date"))
					.toArray();

				if (!dates) return;

				me.make_delivery_note(dates, for_reserved_stock);
				dialog.hide();
			});
			dialog.show();
		} else {
			this.make_delivery_note([], for_reserved_stock);
		}
	}

	make_delivery_note(delivery_dates, for_reserved_stock = false) {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
			frm: this.frm,
			args: {
				delivery_dates,
				for_reserved_stock: for_reserved_stock,
			},
			freeze: true,
			freeze_message: __("Creating Delivery Note ..."),
		});
	}

	make_sales_invoice() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
			frm: this.frm,
		});
	}

	make_maintenance_schedule() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_maintenance_schedule",
			frm: this.frm,
		});
	}

	make_project() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_project",
			frm: this.frm,
		});
	}

	make_inter_company_order() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_inter_company_purchase_order",
			frm: this.frm,
		});
	}

	make_maintenance_visit() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_maintenance_visit",
			frm: this.frm,
		});
	}

	make_purchase_order() {
		let pending_items = this.frm.doc.items.some((item) => {
			let pending_qty = flt(item.stock_qty) - flt(item.ordered_qty);
			return pending_qty > 0;
		});
		if (!pending_items) {
			frappe.throw({
				message: __("Purchase Order already created for all Sales Order items"),
				title: __("Note"),
			});
		}

		var me = this;
		var dialog = new frappe.ui.Dialog({
			title: __("Select Items"),
			size: "large",
			fields: [
				{
					fieldtype: "Check",
					label: __("Against Default Supplier"),
					fieldname: "against_default_supplier",
					default: 0,
				},
				{
					fieldname: "items_for_po",
					fieldtype: "Table",
					label: "Select Items",
					fields: [
						{
							fieldtype: "Data",
							fieldname: "item_code",
							label: __("Item"),
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldtype: "Data",
							fieldname: "item_name",
							label: __("Item name"),
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldtype: "Float",
							fieldname: "pending_qty",
							label: __("Pending Qty"),
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldtype: "Link",
							read_only: 1,
							fieldname: "uom",
							label: __("UOM"),
							in_list_view: 1,
						},
						{
							fieldtype: "Data",
							fieldname: "supplier",
							label: __("Supplier"),
							read_only: 1,
							in_list_view: 1,
						},
					],
				},
			],
			primary_action_label: "Create Purchase Order",
			primary_action(args) {
				if (!args) return;

				let selected_items = dialog.fields_dict.items_for_po.grid.get_selected_children();
				if (selected_items.length == 0) {
					frappe.throw({
						message: "Please select Items from the Table",
						title: __("Items Required"),
						indicator: "blue",
					});
				}

				dialog.hide();

				var method = args.against_default_supplier
					? "make_purchase_order_for_default_supplier"
					: "make_purchase_order";
				return frappe.call({
					method: "erpnext.selling.doctype.sales_order.sales_order." + method,
					freeze_message: __("Creating Purchase Order ..."),
					args: {
						source_name: me.frm.doc.name,
						selected_items: selected_items,
					},
					freeze: true,
					callback: function (r) {
						if (!r.exc) {
							if (!args.against_default_supplier) {
								frappe.model.sync(r.message);
								frappe.set_route("Form", r.message.doctype, r.message.name);
							} else {
								frappe.route_options = {
									sales_order: me.frm.doc.name,
								};
								frappe.set_route("List", "Purchase Order");
							}
						}
					},
				});
			},
		});

		dialog.fields_dict["against_default_supplier"].df.onchange = () => set_po_items_data(dialog);

		function set_po_items_data(dialog) {
			var against_default_supplier = dialog.get_value("against_default_supplier");
			var items_for_po = dialog.get_value("items_for_po");

			if (against_default_supplier) {
				let items_with_supplier = items_for_po.filter((item) => item.supplier);

				dialog.fields_dict["items_for_po"].df.data = items_with_supplier;
				dialog.get_field("items_for_po").refresh();
			} else {
				let po_items = [];
				me.frm.doc.items.forEach((d) => {
					let ordered_qty = me.get_ordered_qty(d, me.frm.doc);
					let pending_qty = (flt(d.stock_qty) - ordered_qty) / flt(d.conversion_factor);
					if (pending_qty > 0) {
						po_items.push({
							doctype: "Sales Order Item",
							name: d.name,
							item_name: d.item_name,
							item_code: d.item_code,
							pending_qty: pending_qty,
							uom: d.uom,
							supplier: d.supplier,
						});
					}
				});

				dialog.fields_dict["items_for_po"].df.data = po_items;
				dialog.get_field("items_for_po").refresh();
			}
		}

		set_po_items_data(dialog);
		dialog.get_field("items_for_po").grid.only_sortable();
		dialog.get_field("items_for_po").refresh();
		dialog.wrapper.find(".grid-heading-row .grid-row-check").click();
		dialog.show();
	}

	get_ordered_qty(item, so) {
		let ordered_qty = item.ordered_qty;
		if (so.packed_items && so.packed_items.length) {
			// calculate ordered qty based on packed items in case of product bundle
			let packed_items = so.packed_items.filter((pi) => pi.parent_detail_docname == item.name);
			if (packed_items && packed_items.length) {
				ordered_qty = packed_items.reduce((sum, pi) => sum + flt(pi.ordered_qty), 0);
				ordered_qty = ordered_qty / packed_items.length;
			}
		}
		return ordered_qty;
	}

	hold_sales_order() {
		var me = this;
		var d = new frappe.ui.Dialog({
			title: __("Reason for Hold"),
			fields: [
				{
					fieldname: "reason_for_hold",
					fieldtype: "Text",
					reqd: 1,
				},
			],
			primary_action: function () {
				var data = d.get_values();
				frappe.call({
					method: "frappe.desk.form.utils.add_comment",
					args: {
						reference_doctype: me.frm.doctype,
						reference_name: me.frm.docname,
						content: __("Reason for hold:") + " " + data.reason_for_hold,
						comment_email: frappe.session.user,
						comment_by: frappe.session.user_fullname,
					},
					callback: function (r) {
						if (!r.exc) {
							me.update_status("Hold", "On Hold");
							d.hide();
						}
					},
				});
			},
		});
		d.show();
	}
	close_sales_order() {
		this.frm.cscript.update_status("Close", "Closed");
	}
	update_status(label, status) {
		var doc = this.frm.doc;
		var me = this;
		frappe.ui.form.is_saving = true;
		frappe.call({
			method: "erpnext.selling.doctype.sales_order.sales_order.update_status",
			args: { status: status, name: doc.name },
			callback: function (r) {
				me.frm.reload_doc();
			},
			always: function () {
				frappe.ui.form.is_saving = false;
			},
		});
	}
};

extend_cscript(cur_frm.cscript, new erpnext.selling.SalesOrderController({ frm: cur_frm }));
