frappe.query_reports["BOM Stock Calculated with Valuation rate"] = {
	filters: [
	    {
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "MultiSelectList",
			options: "Warehouse",
			get_data: function (txt) {
				return frappe.db.get_link_options("Warehouse", txt, {
					is_group: 0,
					custom_is_not_countable:0,
					custom_category:['in',['Ready Stock','Qc','Faulty']]
				});
			},
		},
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
        $(document).on("click", ".create-po", function () {
            let items = [
                {
                    "item_code": $(this).data("item_code"),
                    "qty": parseFloat($(this).data("shortage_qty")).toFixed(3) // Ensuring precision up to 3 decimal places
                }
            ];
            
            frappe.model.with_doctype("Purchase Order", function () {
                let po = frappe.model.get_new_doc("Purchase Order");
        
                frappe.set_route("Form", "Purchase Order", po.name).then(() => {
                 
                    items.forEach(item_data => {
                        let item = frappe.model.add_child(po, "Purchase Order Item", "items");
                        frappe.model.set_value(item.doctype, item.name, "item_code", item_data.item_code);
                        frappe.model.set_value(item.doctype, item.name, "qty", parseFloat(item_data.qty));
                        cur_frm.script_manager.trigger("item_code", item.doctype, item.name);
                    });
            
                    cur_frm.refresh_field("items");
                });
            });
        
        });
		$(document).on("click", ".create-mt", function () {
            let items = [
                {
                    "item_code": $(this).data("item_code"),
                    "qty": parseFloat($(this).data("shortage_qty")).toFixed(3) // Ensuring precision up to 3 decimal places
                }
            ];

            frappe.model.with_doctype("Material Request", function () {
                let mt = frappe.model.get_new_doc("Material Request");
                mt.custom_stock_entry_type_reference = "Material Transfer";
                mt.custom_stock_entry_type_reference = "Material Transfer"
                
                frappe.set_route("Form", "Material Request", mt.name).then(() => {
                    console.log("Form Loaded:", cur_frm);
            
                    items.forEach(item_data => {
                        let item = frappe.model.add_child(mt, "Material Request Item", "items");
                        frappe.model.set_value(item.doctype, item.name, "item_code", item_data.item_code);
                        frappe.model.set_value(item.doctype, item.name, "qty", parseFloat(item_data.qty));
                        cur_frm.script_manager.trigger("item_code", item.doctype, item.name);
                    });
            
                    cur_frm.refresh_field("items");
                });
            });
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