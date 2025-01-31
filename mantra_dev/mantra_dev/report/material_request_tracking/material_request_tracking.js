// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.query_reports["Material Request Tracking"] = {
	"filters": [
		{
            "fieldname": "material_request_id",
            "label": __("Material Request ID"),
            "fieldtype": "MultiSelectList",
			"options": "Material Request",
			get_data: function (txt) {
				return frappe.db.get_link_options("Material Request", txt);
			},
        },
		{
            "fieldname": "material_request_type",
            "label": __("Material Request Type"),
            "fieldtype": "Select",
			"options": "\nPurchase\nMaterial Transfer",
        },
		{
            "fieldname": "material_request_status",
            "label": __("Material Request Status"),
            "fieldtype": "Select",
			"options": "\nDraft\nSubmitted\nStopped\nPending\nPartially Ordered\nPartially Received\nOrdered\nIssued\nTransferred\nReceived",
        },
		{
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            fieldname: "dynamic_field",
            label: __("PO Created By"),
            fieldtype: "Select",
            reqd: 0,
            options: []
        }
	],
	onload: function () {
		$(document).on("click", ".create_material_transfer", function () {
            // Material Transfer Button Click then hit the material pending item qty frappe call and open dailog_box
			var materialRequestId = $(this).data("material_request");
            frappe.call({
                method: "mantra_dev.mantra_dev.report.material_request_tracking.material_request_tracking.get_material_transfer_items",
                args: { docname: materialRequestId },
                callback: function (r) {
                    if (r.message) {
                        let d = new frappe.ui.Dialog({
                            title: 'Material Transfer',
                            fields: [
                                {
                                    label: 'Material Request Id',
                                    fieldname: 'docname',
                                    fieldtype: 'Data',
                                    default: materialRequestId,
                                    read_only: 1
                                },
                                {
                                    label: 'Source Warehouse',
                                    fieldname: 'source_warehouse',
                                    fieldtype: 'Data',
                                    read_only: 1
                                },
                                {
                                    fieldname: "column_break_saffsaf",
                                    fieldtype: "Column Break",
                                },
                                {
                                    label: 'Stock Entry Type Reference',
                                    fieldname: 'stock_entry_type_reference',
                                    fieldtype: 'Link',
                                    options: "Stock Entry Type",
                                    default: "",
                                    read_only: 1,
                                    onchange: function() {
                                        // This Function is Used For When the Stock Entry Referce Type Select then set the source and target warehouse based on that
                                        let stock_entry_type = d.get_value('stock_entry_type_reference');
                                        if (stock_entry_type) {
                                            frappe.call({
                                                method: 'frappe.client.get_value',
                                                args: {
                                                    doctype: 'Stock Entry Type',
                                                    filters: { name: stock_entry_type },
                                                    fieldname: ['custom_source_warehouse', 'custom_target_warehouse']
                                                },
                                                callback: function(response) {
                                                    d.set_value('source_warehouse', response.message.custom_source_warehouse);
                                                    d.set_value('target_warehouse', response.message.custom_target_warehouse);
                                                }
                                            });
                                        }
                                    }
                                },
                                {
                                    label: 'Target Warehouse',
                                    fieldname: 'target_warehouse',
                                    fieldtype: 'Data',
                                    read_only: 1
                                },
                                {
                                    label: 'Material Transfer Items Detials',
                                    fieldname: 'section_break_dsgiod',
                                    fieldtype: 'Section Break',
                                },
                                {
                                    "label": 'Transfer Qty',
                                    "fieldname": 'transfer_qty_table',
                                    "fieldtype": 'Table',
                                    "read_only": true,
                                    "cannot_add_rows": true,
                                    "cannot_delete_rows": true,
                                    "data": r.message,
                                    "fields": [
                                        {
                                            fieldname: "item_code",
                                            label: __("Item Code"),
                                            fieldtype: "Link",
                                            options: "Item",
                                            in_list_view: 1,
                                            read_only: 1
                                        },
                                        {
                                            fieldname: "item_name",
                                            label: __("Item Name"),
                                            fieldtype: "Data",
                                            in_list_view: 1,
                                            read_only: 1
                                        },
                                        {
                                            fieldname: "transfer_qty",
                                            label: __("Transfer Qty"),
                                            fieldtype: "Float",
                                            in_list_view: 1,
                                            read_only: 1
                                        },
                                    ],
                                }
                            ],
                            size: 'medium',
                            primary_action_label: 'Submit',
                            primary_action(values) {
                                // When Submit the material transfer entry dailog box then auto creation of material transfer request frappe call and received message of that material request sucessfully message
                                d.get_primary_btn().prop('disabled', true);
                                frappe.dom.freeze(__('Processing Material Transfer...'));

                                frappe.call({
                                    method: "mantra_dev.mantra_dev.report.material_request_tracking.material_request_tracking.make_material_transfer_material_request",
                                    args: {
                                        docname: materialRequestId,
                                        items: values.transfer_qty_table,
                                        source_warehouse: values.source_warehouse,
                                        target_warehouse: values.target_warehouse,
                                        stock_entry_type_reference: values.stock_entry_type_reference
                                    },
                                    callback: function (r) {
                                        if (r.message.status === "success") {
                                            frappe.msgprint(__(r.message.message));
                                            frappe.query_report.refresh();
                                        }else if (r.message.status === "error"){
                                            frappe.throw(__(r.message.message));
                                            frappe.query_report.refresh();
                                        }
                                    },
                                    error: function () {
                                        frappe.msgprint(__("An error occurred while approving the Material Transfer."));
                                    },
                                    always: function () {
                                        // Unfreeze the screen and re-enable the primary button
                                        frappe.dom.unfreeze();
                                    }
                                });
                                d.hide();
                            }
                        });
                        
                        d.set_value('stock_entry_type_reference', "Transfer to Employee");
                        d.fields_dict.transfer_qty_table.grid.refresh();
                        d.show();

                    }
                },
                error: function () {
                    frappe.msgprint(__("An error occurred while fetching material transfer items."));
                }
            });
		})
		$(document).on("click", ".received_material", function () {
			var materialRequestId = $(this).data("material_request");
            materialRequestId = materialRequestId.split(',');
            // When Submit the material transfer entry is received then verify and auto submit that stock entry against that and return sucess message
            frappe.call({
                method: "mantra_dev.mantra_dev.report.material_request_tracking.material_request_tracking.submit_material_request_stock_entry",
                args: {
                    docname_list: materialRequestId
                },
                callback: function (r) {
                    if (r.message.status === "success") {
                        frappe.msgprint(__(r.message.message));
                        frappe.query_report.refresh();
                    }else if (r.message.status === "error"){
                        frappe.throw(__(r.message.message));
                        frappe.query_report.refresh();
                    }
                },
                error: function () {
                    frappe.msgprint(__("An error occurred while submitting the stock entry."));
                }
            });
		})
	},
	"formatter": function (value, row, column, data, default_formatter) {
        // Bold the Main Material Request Row Text Bold
        value = default_formatter(value, row, column, data);
        if (data && data["indent"] === 0) {
			value = `<strong>${value}</strong>`;
		}
        return value;
    }
};
