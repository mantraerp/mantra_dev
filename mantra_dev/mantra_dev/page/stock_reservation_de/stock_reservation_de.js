frappe.pages['stock-reservation-de'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Stock Reservation Details',
        single_column: true
    });

    $(frappe.render_template("billing_rate_leaderb", { })).appendTo(page.body);

	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Item",
			fields: ["name"],
		},
		callback: function(response) {
			if (response && response.message) {
				let itemoption = response.message.map(item => item.name);
				let fields = [
					{
						"fieldname": "item",
						"label": __("Item"),
						"fieldtype": "Select",
						"options": itemoption,
						// "default": frappe.defaults.get_user_default("Company")
					},
					// {
					// 	"fieldname": "date_filter",
					// 	"label": __("Timespan"),
					// 	"fieldtype": "Select",
					// 	"options": "This Year\nThis Month\nThis Week\nToday\nYesterday\nLast Week\nLast Month\nLast 3 Months\nLast 6 Months\nLast Year\nSelect Date Range",
					// 	"default": "This Year",
					// },
					// {
					// 	label: 'From Date',
					// 	fieldtype: 'Date',
					// 	fieldname: 'from_date',
					// 	hidden: 1,
					// 	default: frappe.datetime.nowdate()
					// },
					// {
					// 	label: 'To Date',
					// 	fieldtype: 'Date',
					// 	fieldname: 'to_date',
					// 	hidden: 1,
					// 	default: frappe.datetime.nowdate()
					// },
				];
				// var date_filter = "This Year";
				// var company = frappe.defaults.get_user_default("Company");
				// var from_date = frappe.datetime.nowdate();
				// var to_date = frappe.datetime.nowdate();
				// updateLeaderboard(date_filter, company, from_date, to_date);

				// fields.forEach(field => {
				// 	let filterField = page.add_field(field);
				// 	filterField.$input.on('change', function() {
				// 		var changing_value = filterField.get_value();
				// 		if (field.fieldname === 'from_date') {
				// 			from_date = changing_value;
				// 		} else if (field.fieldname === 'to_date') {
				// 			to_date = changing_value;
				// 		} else if (field.fieldname === 'date_filter') {
				// 			date_filter = changing_value;
				// 			if (date_filter === "Select Date Range") {
				// 				page.fields_dict.from_date.df.hidden = 0;
				// 				page.fields_dict.to_date.df.hidden = 0;
				// 			} else {
				// 				page.fields_dict.from_date.df.hidden = 1;
				// 				page.fields_dict.to_date.df.hidden = 1;
				// 			}
				// 			page.fields_dict.from_date.$input.off('change');
				// 			page.fields_dict.to_date.$input.off('change');
				// 			page.fields_dict.from_date.refresh();
				// 			page.fields_dict.to_date.refresh();
				// 			page.fields_dict.from_date.$input.on('change', function() {
				// 				from_date = page.fields_dict.from_date.get_value();
				// 				updateLeaderboard(date_filter, company, from_date, to_date);
				// 			});
				// 			page.fields_dict.to_date.$input.on('change', function() {
				// 				to_date = page.fields_dict.to_date.get_value();
				// 				updateLeaderboard(date_filter, company, from_date, to_date);
				// 			});
				// 		} else if (field.fieldname === 'company') {
				// 			company = changing_value;
				// 		}
				// 		updateLeaderboard(date_filter, company, from_date, to_date);
					// });
				// });
					
			}
		}
	});
	
    // Function to fetch and update the leaderboard
    function updateLeaderboard(date_filter, company, from_date, to_date) {
		$(page.main).find('.table-container').empty();
			frappe.call({
				method: "project_management.project_management.page.billing_rate_leaderb.billing_rate_leaderb.get_task_totals",
				args: {
					date_filter: date_filter,
					company: company,
					from_date: from_date,
					to_date: to_date
				},
				callback: function (response) {
					var data = response.message;		

					var rankers = $('<div class="Main shadow-lg rounded border flex justify-content-around py-4">');
					if (Object.keys(data).length === 0) {
						rankers.append(`
							<H2 style="margin-top:25vh; margin-bottom:25vh;">There is no employee data available.</H2>
						`);
					}
					var rank = 0;
					var borderColors = ['gold', 'silver', '#CD7F32'];
					$.each(data, function (index, item) {
						rank++;
						if (rank <= 3) {
							var borderColor = borderColors[rank - 1];
							rankers.append(`
								<div class="text-center w-100" style="position: relative;">
									<div style="border: 2px solid ${borderColor};" class="rankers-image mx-auto">
										<img src="${item.image}" alt="" style="border-radius: 10%; height: 100%;">
									</div>
									<h3 class="my-2" style="">${item.employee_name}</h3>
									<div class="" style="border-radius: 20%; position: absolute; top: 50%; left: 46%;  background-color: ${borderColor};">
										<p class="rank-design" style="background-color: ${borderColor}; border: 2px solid white; margin: 2px">#${rank}</p>
									</div>
									<p class="my-0 h5 text-secondary">${item.on_time_completed} / ${item.task_count} (${item.percentage_on_time_completed}%)</p>
								</div>
							`);
						}
					});
					rankers.append(`
						</div>
					`);
					$(page.main).find('.table-container').append(rankers);
		
					var tableContainer = $('<div class="table-container" style="height: 600px; overflow-y: auto;"></div>');
					var table = $('<table class="Main shadow-lg rounded border" style=""></table>');
		
					var rank = 0;
					$.each(data, function (index, item) {
						rank++;
						if (rank > 3) {
							if (rank == 4){
								table.append(`
									<tr>
										<th width=100>Rank</th>
										<th width=60></th>
										<th width=150 style="text-align:left;">Name</th>
										<th width=200>Task Count</th>
										<th width=200>On Time Completed</th>
										<th width=200>Percentage on Time Completed</th>
									</tr>
								`);
							}
							var row = `
								<tr ${rank % 2 === 1 ? 'style="background-color: #f8fafd;"' : ''}>
									<td>${rank}</td>
									<td><img src="${item.image}" alt="h" class="employee-image" onerror="this.onerror=null; this.src='/private/files/Ellipse36.svg';"></td>
									<td class="empname">${item.employee_name}</td>
									<td>${item.task_count}</td>
									<td>${item.on_time_completed}</td>
									<td>${item.percentage_on_time_completed}%</td>
								</tr>
							`;
							table.append(row);
						}
					});
		
					tableContainer.append(table);
					$(page.main).find('.table-container').append(tableContainer);
				}
			});
    }
}
