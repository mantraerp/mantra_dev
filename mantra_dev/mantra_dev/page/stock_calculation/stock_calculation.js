frappe.pages['stock-calculation'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Bom Stock Calculation Tool',
        single_column: true
    });
    page.body.empty()
    const calculateButton = page.add_inner_button('Calculate', () => {
        // Collect data from the table
        let data = [];
        let itemCodes = [];  // To keep track of already selected items
        let duplicateItemFound = false;
        let invalidRowFound = false;  // To track if any row is invalid
        $('#bom_stock_table tbody tr').each(function() {
            let row = {
                item: $(this).find('.item-link').val(),
                bom: $(this).find('.bom-link').val(),
                qty: parseFloat($(this).find('.qty').val()) || 0
            };
            if (!row.item || !row.bom || row.qty <= 0) {
                invalidRowFound = true;  // Mark that an invalid row is found
                return false;  // Break out of the loop
            }
            if (row.item && row.bom) {
                // Check if the item already exists in the data array
                if (itemCodes.includes(row.item)) {
                    duplicateItemFound = true; // Mark that a duplicate item is found
                    return false;  // Break out of the loop
                }
                itemCodes.push(row.item);  // Add the item to the list of selected items
                data.push(row);  // Add the row to the data array
            }
        });
        if (invalidRowFound) {
            frappe.msgprint(__('Please ensure all rows have a valid Item, BOM, and Quantity.'));
            return;
        }
        if (duplicateItemFound) {
            frappe.msgprint(__('Duplicate item found. Please ensure each item is entered only once.'));
            return;
        }
        if (data.length === 0) {
            frappe.msgprint(__('No valid data found in the table.'));
            return;
        }
		frappe.route_options = {
			data: JSON.stringify(data)
		};
        // Pass the data to the report
        frappe.open_in_new_tab = true;
        frappe.set_route('query-report','BOM Stock Calculated with Valuation rate');
    });
    // Create a child table dynamically on the page with a checkbox and delete button
    var table_html = `
        <table class="table table-bordered" id="bom_stock_table">
            <thead>
                <tr>
                    <th width="1%"></th>
                    <th width="25%">Item</th>
                    <th width="25%">BOM</th>
                    <th width="24%">Qty</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td width="1%"><input type="checkbox" class="row-checkbox"></td>
                    <td width="25%"><select class="form-control item-link"></select></td>
                    <td width="25%"><select type="text" class="form-control bom-link" placeholder="Select BOM"></td>
                    <td width="24%"><input type="number" class="form-control qty" value="1" placeholder="Enter Qty"></td>
                </tr>
            </tbody>
        </table>
        <button class="btn btn-primary" id="add_row">Add Row</button>
        <button class="btn btn-danger" id="delete_selected" style="display: none;">Delete</button>`;
    page.body.html(table_html);
    var filters = {
		'is_stock_item': 1,
		'disabled': 0,
        'workflow_state':'Approved'
	};
    // Populate the Item field with all items from the Item doctype
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Item',
            fields: ['item_name'],
			limit_page_length: 1000,
			filters:filters
        },
        callback: function(response) {
            var items = response.message;
            var itemSelect = $('#bom_stock_table tbody tr td .item-link');
			itemSelect.append('<option value="">Select Item</option>');
            items.forEach(function(item) {
                itemSelect.append('<option value="' + item.item_name + '">' + item.item_name + '</option>');
            });
        }
    });
    // Handle the addition of rows dynamically
    $('#add_row').on('click', function() {
        var newRow = `
            <tr>
                <td><input type="checkbox" class="row-checkbox"></td>
                <td><select class="form-control item-link"></select></td>
                <td><select type="text" class="form-control bom-link" placeholder="Select BOM"></td>
                <td><input type="number" class="form-control qty" value="1" placeholder="Enter Qty"></td>
            </tr>`;
        // Append the new row to the table body
        $('#bom_stock_table tbody').append(newRow);
        var filters = {
            'is_stock_item': 1,
            'disabled': 0,
            'workflow_state':'Approved'
        };
        // Fetch items and populate the select field for the new row
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Item',
                fields: ['item_name'],
                // limit_page_length: 1000,
                filters:filters
            },
            callback: function(response) {
                var items = response.message;
                // Find the item select field in the newly added row
                var itemSelect = $('#bom_stock_table tbody tr:last-child .item-link');
                // Append options to the select field
                itemSelect.append('<option value="">Select Item</option>');
                items.forEach(function(item) {
                    itemSelect.append('<option value="' + item.item_name + '">' + item.item_name + '</option>');
                });}});
    });
    $('#bom_stock_table tbody').on('click', '.bom-link', function() {
        var bomField = $(this);
        var selectedItem = $(this).closest('tr').find('.item-link').val(); // Get the selected item for the current row
    
        if (!selectedItem) {
            // If no item is selected, show a message and prevent further action
            frappe.msgprint(__('Please select an Item before choosing a BOM.'));
            bomField.blur(); // Remove focus from the BOM field
            return false; // Prevent the default click action
        }
    });
    
    $('#bom_stock_table tbody').on('change', '.item-link', function() {
        var selectedItem = $(this).val(); // Get the selected item
        // Find the BOM field for the current row
        var bomSelect = $(this).closest('tr').find('.bom-link');
        // Reset BOM options (clear the BOM select field)
        bomSelect.empty();
        bomSelect.append('<option value="">Select BOM</option>'); // Add a default "Select BOM" option
        if (selectedItem) {
            // Fetch BOMs for the selected item
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: "BOM",
                    filters: { 'item_name': selectedItem , docstatus:["!=",2] }, // Filter BOMs by selected item
                    fields: ['name']
                },
                callback: function(response) {
                    var boms = response.message;
                    if (boms.length > 0) {
                        // Enable the BOM field after fetching the BOMs
                        bomSelect.prop('disabled', false);
                        // Populate BOM options
                        boms.forEach(function(bom) {
                        bomSelect.append('<option value="' + bom.name + '">' + bom.name + '</option>');
                        });
                    } else {
                        // If no BOMs are found, show "No BOM found" option
                        bomSelect.empty();
                        bomSelect.append('<option value="">No BOM found</option>');
                        bomSelect.prop('disabled', true); // Optionally keep the field disabled
                    }
                }
            });
        } else {
            bomSelect.prop('disabled', true); // Disable BOM field if no item is selected
        }
    });
    // Show or hide the "Delete Selected" button based on checked checkboxes
    $('#bom_stock_table').on('change', '.row-checkbox', function() {
        var anyChecked = $('#bom_stock_table .row-checkbox:checked').length > 0;
        if (anyChecked) {
            $('#delete_selected').show(); // Show the button if any row is checked
        } else {
            $('#delete_selected').hide(); // Hide the button if no row is checked
        }
    });
    // Handle the delete selected rows functionality
    $('#delete_selected').on('click', function() {
        $('#bom_stock_table tbody tr').each(function() {
            var checkbox = $(this).find('.row-checkbox');
            if (checkbox.prop('checked')) {
                $(this).remove(); // Remove the row if the checkbox is checked
            }
        });
        // After deleting rows, check if any checkbox is still checked and toggle the button
        var anyChecked = $('#bom_stock_table .row-checkbox:checked').length > 0;
        if (!anyChecked) {
            $('#delete_selected').hide(); // Hide the button if no row is checked
        }
    });
};

