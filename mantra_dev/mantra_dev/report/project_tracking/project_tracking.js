frappe.query_reports["Project Tracking"] = {
	filters: [
	   
		{
            "fieldname": "from_date",
            "label": __("Date"),
            "fieldtype": "Date",
			default: frappe.datetime.get_today()
        },
		{
			fieldname: "route_data",
			label: __("Route Data"),
			fieldtype: "Data",
			hidden:1,
			default: frappe.route_options && frappe.route_options.data,
		}
	],
	onload: function () {
        $(document).off("click", ".create-po").on("click", ".create-po", function () {
            let items = [
                {
                    "item_code": $(this).data("item_code"),
                    "qty": parseFloat($(this).data("shortage_qty")).toFixed(2) 
                }
            ];
            
            frappe.model.with_doctype("Purchase Order", function () {
                let po = frappe.model.get_new_doc("Purchase Order");
        
                frappe.set_route("Form", "Purchase Order", po.name).then(() => {
                 
                    items.forEach(item_data => {
                        let item = frappe.model.add_child(po, "Purchase Order Item", "items");
                        frappe.model.set_value(item.doctype, item.name, "item_code", item_data.item_code);
                        frappe.model.set_value(item.doctype, item.name, "qty", parseFloat(item_data.qty).toFixed(2));
                        cur_frm.script_manager.trigger("item_code", item.doctype, item.name);
                    });
            
                    cur_frm.refresh_field("items");
                });
            });
        
        });
		$(document).off("click", ".create-mt").on("click", ".create-mt", function () {
            let items = [
                {
                    "item_code": $(this).data("item_code"),
                    "qty": parseFloat($(this).data("shortage_qty")).toFixed(3) 
                }
            ];

            frappe.model.with_doctype("Material Request", function () {
                let mt = frappe.model.get_new_doc("Material Request");
                mt.custom_stock_entry_type_reference = "Material Transfer";
                mt.custom_stock_entry_type_reference = "Material Transfer"
                
                frappe.set_route("Form", "Material Request", mt.name).then(() => {
            
                    items.forEach(item_data => {
                        let item = frappe.model.add_child(mt, "Material Request Item", "items");
                        frappe.model.set_value(item.doctype, item.name, "item_code", item_data.item_code);
                        frappe.model.set_value(item.doctype, item.name, "qty", parseFloat(item_data.qty).toFixed(2));
                        cur_frm.script_manager.trigger("item_code", item.doctype, item.name);
                    });
            
                    cur_frm.refresh_field("items");
                });
            });
        });
        $(document).off("click", ".create-wo").on("click", ".create-wo", function () {
            let table_instance = frappe.query_report.datatable;
            let row_data = table_instance.datamanager.data.find(row => 
                row.raw_material_item === $(this).data("item_code")
            );
        
            if (!row_data) {
                frappe.msgprint("Could not retrieve row data.");
                return;
            }
            open_work_order_dialog(row_data);
        });
    },
    after_datatable_render: function (table_instance) {
        table_instance.datamanager.data.forEach((row, rowIdx) => {
            if (row['shortage_qty'] > 0) {
                color_single_row(table_instance, rowIdx,'#ff000040 !important');
            }
			else {
				color_single_row(table_instance, rowIdx, 'transparent !important'); // Reset to default
			}
        });
    }
};

function color_single_row(table_instance, rowIdx,color) {
    for (let col = 0; col < Object.entries(table_instance.datamanager.columns).length; col++) {
        table_instance.style.setStyle(`.dt-cell--${col}-${rowIdx}`, { backgroundColor: `${color}` });
    }
}


function open_work_order_dialog(row_data) {
    let item_options = [];
    
    // Collect finished goods from row_data (all keys except raw_material_item & metadata columns)
    for (let key in row_data) {
        if (!["raw_material_item", "total_qty", "available_qty", "reserve_qty", "transit_qty", "shortage_qty", "valuation_rate","create_material_transfer","create_purchase_order","create_work_order","item_code"].includes(key)) {
            item_options.push({
                label: key, 
                value: key
            });
        }
    }

    if (item_options.length === 0) {
        frappe.msgprint(__("No finished goods found in this row."));
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __("Create Work Order"),
        fields: [
            {
                label: __("Finished Good Item"),
                fieldname: "finished_good",
                fieldtype: "Select",
                options: item_options.map(opt => opt.value),
                reqd: 1
            },
            {
                label: __("Quantity"),
                fieldname: "qty",
                fieldtype: "Float",
                read_only:1,
                reqd: 1
            }
        ],
        primary_action_label: __("Create"),
        primary_action(values) {
            create_work_order(values.qty, values.finished_good);
            dialog.hide();
        }
    });

    // Set initial qty based on selected item
    dialog.fields_dict.finished_good.df.onchange = function () {
        let selected_item = dialog.get_value("finished_good");
        if (selected_item) {
            dialog.set_value("qty", row_data[selected_item]);
        }
    };

    dialog.show();
}



function create_work_order(qty, row_material_item) {
    frappe.model.with_doctype("Work Order", function () {
        let wo = frappe.model.get_new_doc("Work Order");
        frappe.set_route("Form", "Work Order", wo.name).then(() => {
            frappe.model.set_value("Work Order", wo.name, "production_item", row_material_item);
            frappe.model.set_value("Work Order", wo.name, "qty", qty.toFixed(2));
            cur_frm.script_manager.trigger("production_item", "Work Order", wo.name);
        });
    });
}
