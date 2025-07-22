frappe.pages['stock-calculation'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Bom Stock Calculation Tool',
        single_column: true
    });

    page.body.empty();

    const calculateButton = page.add_inner_button('Calculate', () => {
        let data = [];
        let itemCodes = [];
        let duplicateItemFound = false;
        let invalidRowFound = false;

        $('#bom_stock_table tbody tr').each(function() {
            let item = $(this).find('.item-cell input').val();
            let bom = $(this).find('.bom-cell input').val();
            let qty = parseFloat($(this).find('.qty-cell input').val()) || 0;

            if (!item || !bom || qty <= 0) {
                invalidRowFound = true;
                return false;
            }

            if (itemCodes.includes(item)) {
                duplicateItemFound = true;
                return false;
            }

            itemCodes.push(item);
            data.push({ item, bom, qty });
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

        frappe.route_options = { data: JSON.stringify(data) };
        frappe.open_in_new_tab = true;
        frappe.set_route('query-report', 'BOM Stock Calculated with Valuation rate');
    });

    const table_html = `
        <table class="table table-bordered" id="bom_stock_table">
            <thead>
                <tr>
                    <th width="1%"></th>
                    <th width="25%">Item</th>
                    <th width="25%">BOM</th>
                    <th width="24%">Qty</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
        <button class="btn btn-primary" id="add_row">Add Row</button>
        <button class="btn btn-danger" id="delete_selected" style="display: none;">Delete</button>
    `;

    page.body.html(table_html);

    function add_row() {
        const $row = $(`
            <tr>
               <td style="vertical-align: middle; text-align: center;">
                    <input type="checkbox" class="row-checkbox">
                </td>
                <td class="item-cell"></td>
                <td class="bom-cell"></td>
                <td class="qty-cell"></td>
            </tr>
        `);
        $('#bom_stock_table tbody').append($row);

       
        frappe.ui.form.make_control({
            parent: $row.find('.item-cell'),
            df: {
                fieldtype: 'Link',
                options: 'Item',
                only_select:true,
                fieldname: 'item_code',
                
                get_query: () => ({
                    filters: {
                        is_stock_item: 1,
                        disabled: 0,
                        workflow_state: 'Approved'
                    }
                })
            },
            render_input: true
        });

        
        frappe.ui.form.make_control({
            parent: $row.find('.bom-cell'),
            df: {
                fieldtype: 'Link',
                options: 'BOM',     
                fieldname: 'bom_code',
                only_select: true,
              
                get_query: function () {
                    let selected_item = $row.find('.item-cell input').val();
                    if (!selected_item) {
                        frappe.msgprint(__('Please select an Item before choosing a BOM.'));
                        return { filters: { name: '' } };
                    }
                    return {
                        filters: {
                            item: selected_item,
                            docstatus: ["!=", 2]
                        }
                    };
                }
            },
            render_input: true
        });

        frappe.ui.form.make_control({
            parent: $row.find('.qty-cell'),
            df: {
                fieldtype: 'Float',
                fieldname: 'qty',
                default: 1
            },
            render_input: true
        });
    }

    
    add_row();

    $('#add_row').on('click', function () {
        add_row();
    });

    $('#bom_stock_table').on('change', '.row-checkbox', function () {
        const anyChecked = $('#bom_stock_table .row-checkbox:checked').length > 0;
        $('#delete_selected').toggle(anyChecked);
    });

    $('#delete_selected').on('click', function () {
        $('#bom_stock_table .row-checkbox:checked').each(function () {
            $(this).closest('tr').remove();
        });
        $('#delete_selected').hide();
    });
};
