frappe.query_reports["BOM Stock Calculated with Valuation rate"] = {
	filters: [
	    {
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: () => {
				return {
					filters: {
						"is_group": 0
					}
				};
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
};
