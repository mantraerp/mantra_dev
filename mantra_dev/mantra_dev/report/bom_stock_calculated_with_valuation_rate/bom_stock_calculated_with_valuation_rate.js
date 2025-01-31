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
					custom_is_not_countable:1,
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
	console.log(table_instance)
    for (let col = 0; col < Object.entries(table_instance.datamanager.columns).length; col++) {
        table_instance.style.setStyle(`.dt-cell--${col}-${rowIdx}`, { backgroundColor: `${color}` });
    }
}