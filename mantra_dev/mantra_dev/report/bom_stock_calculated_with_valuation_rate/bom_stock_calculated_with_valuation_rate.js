frappe.query_reports["BOM Stock Calculated with Valuation rate"] = {
	filters: [
		{
			fieldname: "bom",
			label: __("BOM"),
			fieldtype: "MultiSelectList",
			default:"",
			get_data: function (txt) {
				return new Promise((resolve, reject) => {
					frappe.call({
						method: "frappe.client.get_list",
						args: {
							doctype: "BOM",
							filters: {
								name: ["like", "%" + txt + "%"]
							},
							fields: ["name"],
							limit: 10
						},
						callback: function (r) {
							if (r.message) {
								let value_list = [];
								r.message.forEach(function (d) {
									value_list.push({ "value": d.name, "description": d.name });
								});
								resolve(value_list);
							} else {
								resolve([]);
							}
						},
						error: function (err) {
							reject(err);
						}
					});
				});
			}
		},
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
			fieldname: "qty_to_make",
			label: __("Quantity to Make"),
			fieldtype: "Float",
			default: 1.0,
			reqd: 1,
		},
		{
			fieldname: "show_exploded_view",
			label: __("Show exploded view"),
			fieldtype: "Check",
			default: 0,
		},
	],
};
