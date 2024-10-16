frappe.ui.form.on('Material Request', {
    refresh(frm) {
        // if(frm.doc.docstatus==0 && !frm.is_new()){
            // if(frappe.user_roles.includes("Item Requester") == false){
            frm.add_custom_button(__('Item Code Request'), function () {
                // Call custom function when button is clicked
                openQuickEntryForm(frm);
            });
        // }
        // }
        if (cur_frm.doc.transfer_status == "In Transit") {
            frappe.call({
                method: "mantra_dev.backend_code.material_request.get_target_warehouse_deatils",
                args: {
                    warehouse_nm: cur_frm.doc.set_warehouse
                },
                callback: function (r) {
                    if (!r.exc) {
                        console.log(r.message);
                        if (r.message.includes(frappe.session.logged_in_user)) {
                            console.log("user login");
                            frm.add_custom_button(__('End Transit'), function () {

                                frappe.model.open_mapped_doc({
                                    method: "mantra_dev.backend_code.material_request.make_stock_in_entry",
                                    frm: frm,
                                })
                            });
                        } else {
                            console.log("user not authorized");
                        }
                    } else {
                        console.log("Error fetching warehouse details:", r.exc);
                    }
                }
            });
        }
    }
});
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
                                            "form_type": "Material Request",
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
        throw new Error("Invalid type specified. Use 'keys' or 'values'.");
    }
}
