// // Copyright (c) 2024, Foram Shah and contributors
// // For license information, please see license.txt

// frappe.query_reports["Stock Reservation Details"] = {
// 	"filters": [

// 	]
// };
// /// Copyright (c) 2024, Foram Shah and contributors
// // For license information, please see license.txt

frappe.query_reports["Stock Reservation Details"] = {
	"filters": [
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
		},
		{
			fieldname: "set_warehouse",
			fieldtype: "Link",
			label: __("Set Warehouse"),
			options: "Warehouse",
			// default: frm.doc.set_warehouse,
			get_query: () => {
				return {
					filters: [["Warehouse", "is_group", "!=", 1]],
				};
			},
			// onkeyup: () => {
				// alert("hello")
			// },
		},
		{
			fieldname: "total_qty",
			fieldtype: "Float",
			label: __("Total Qty")
		}
	]
};
$(document).on("click", ".reserv_qty", function () {
	var button = $(this);
	var attributes = button.data(); 
	console.log(attributes)
	// Fetch all data attributes as an object
	// frappe.msgprint("Reserve button clicked! Attributes: " + JSON.stringify(attributes));
	const dialog = new frappe.ui.Dialog({
		title: __("Stock Reservation"),
		size: "extra-large",
		fields: [
			{
				fieldname: "warehouse",
				fieldtype: "Link",
				label: __("Set Warehouse"),
				options: "Warehouse",
				default: attributes.warehouse,
				read_only: 1
			},
			{
				fieldname: "so_id",
				fieldtype: "Link",
				label: __("Sales Order Id"),
				options: "Sales Order",
				default: attributes.salesOrderId,
				read_only: 1
			},
			{
				fieldname: "line_id",
				fieldtype: "Link",
				label: __("Line Item Id"),
				options: "Sales Order Item",
				default: attributes.id,
				read_only: 1,
				hidden:1
			},
			{
				fieldname: "item_code",
				fieldtype: "Data",
				label: __("Item Code"),
				default: attributes.itemCode,
				read_only: 1
				
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "customer",
				fieldtype: "Data",
				label: __("Customer Name"),
				default: attributes.customer,
				read_only: 1
			},
			{
				fieldname: "so_date",
				fieldtype: "Date",
				label: __("Orderd Date"),
				default: attributes.soDate,
				read_only: 1
			},
			
			{
				fieldname: "total_qty",
				fieldtype: "Float",
				label: __("Total Qty"),
				default: attributes.qty,
				read_only: 1
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "reserved_qty",
				fieldtype: "Float",
				label: __("Reserved Qty"),
				default: attributes.reservedQty,
				read_only: 1
			},
			{
				fieldname: "to_reserved_qty",
				fieldtype: "Float",
				label: __("To Reserved Qty"),
				reqd:1,
				read_only: 0,
				default: attributes.toReserveQty,
			},
			// {
			// 	fieldname: "to_reserved",
			// 	fieldtype: "Float",
			// 	label: __("To Reserved Qty"),
			// 	reqd:1,
			// 	read_only: 1,
			// 	default: attributes.toReserveQty,
			// },
			{
				fieldname: "delivery_date",
				fieldtype: "Date",
				label: __("Dispatch Date"),
				read_only: 0,
				reqd:1
			},
			
		],// Add comma here
		primary_action_label: __("Reserve Stock"),
		primary_action: () => {
			var values = dialog.get_values(); // Get values of all fields in the dialog
				var items=[{
					"delivery_date": values.delivery_date,
					"idx": 1,
					"item_code": values.item_code,
					"name": "row 1",
					// "pending_qty": values.to_reserved_qty,
					"qty_to_reserve": values.to_reserved_qty,
					"sales_order_item": values.line_id,
					"total_qty": values.total_qty,
					"warehouse": values.warehouse,
					"__checked": 1
				}]
			if (items) {
				if(items[0].to_reserved_qty<=0){
				}
				else{
					console.log(items)
					// frappe.db.set_value("Sales Order Item",items[0].sales_order_item,"custom_pending_qty",/)
					// Now you can use these values as needed,
					// For example, you can make an AJAX call to handle the reservation
					frappe.call({
						// Assuming frm is defined elsewhere
						method: "mantra_dev.backend_code.stock_reservation_on_report.create_stock_reservation_entries",
						args: {
							values:items,
							doc:values.so_id
						},
						freeze: true,
						freeze_message: __("Reserving Stock..."),
						callback: (r) => {
							window.location.reload()
							// frm.doc.__onload.has_unreserved_stock = false;
							// frm.reload_doc();
						},
					});
				}
		
				dialog.hide();
			} else {
				frappe.msgprint(__("Please fill all required fields."));
			}
		},
		
	});	
	dialog.show();


});

$(document).on("click", ".unreserv_qty", function () {
	var button = $(this);
	var attributes = button.data(); // Fetch all data attributes as an object

		const dialog = new frappe.ui.Dialog({
			title: __("Stock Unreservation"),
			size: "extra-large",
			fields: [
				{
					fieldname: "sr_entries",
					fieldtype: "Table",
					label: __("Reserved Stock"),
					allow_bulk_edit: false,
					cannot_add_rows: true,
					cannot_delete_rows: true,
					in_place_edit: true,
					data: [],
					fields: [
						{
							fieldname: "sre",
							fieldtype: "Link",
							label: __("Stock Reservation Entry"),
							options: "Stock Reservation Entry",
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldname: "item_code",
							fieldtype: "Link",
							label: __("Item Code"),
							options: "Item",
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldname: "warehouse",
							fieldtype: "Link",
							label: __("Warehouse"),
							options: "Warehouse",
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
						{
							fieldname: "qty",
							fieldtype: "Float",
							label: __("Qty"),
							reqd: 1,
							read_only: 1,
							in_list_view: 1,
						},
					],
				},
			],
			primary_action_label: __("Unreserve Stock"),
			primary_action: () => {
				var data = { sr_entries: dialog.fields_dict.sr_entries.grid.get_selected_children() };

				if (data.sr_entries && data.sr_entries.length > 0) {
					frappe.call({
						// doc: frm.doc,
						method: "mantra_dev.backend_code.stock_reservation_on_report.cancel_stock_reservation_entrie",
						args: {
							doc:attributes.salesOrderId,
							sre_list: data.sr_entries.map((item) => item.sre)
						},
						freeze: true,
						freeze_message: __("Unreserving Stock..."),
						callback: (r) => {
							// frm.doc.__onload.has_reser														ved_stock = false;
							// frm.reload_doc();
							window.location.reload()
						},
					});

					dialog.hide();
				} else {
					frappe.msgprint(__("Please select items to unreserve."));
				}
			},
		});

		frappe
			.call({
				method: "erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry.get_stock_reservation_entries_for_voucher",
				args: {
					voucher_type: "Sales Order",
					voucher_no: attributes.salesOrderId,
				},
				callback: (r) => {
					if (!r.exc && r.message) {
						r.message.forEach((sre) => {
							console.log(sre)
							if(sre.voucher_detail_no==attributes.id){
							if (flt(sre.reserved_qty) > flt(sre.delivered_qty)) {
								dialog.fields_dict.sr_entries.df.data.push({
									sre: sre.name,
									item_code: sre.item_code,
									warehouse: sre.warehouse,
									qty: flt(sre.reserved_qty) - flt(sre.delivered_qty),
								});
							}
						}
						});
					}
				},
			})
			.then((r) => {
				dialog.fields_dict.sr_entries.grid.refresh();
				dialog.show();
			});
	
});
