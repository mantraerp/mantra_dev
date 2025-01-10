
// frappe.listview_settings['Item'] = {
//     onload: function(listview) {
//         // Adjust column widths
//         // listview.page.add_custom_button('Customize Columns', () => {
//         //     console.log("Customize columns button clicked");
//         // });

//         // Define custom widths for specific fields
//         const custom_columns = {
//             // item_name: "400%",
//             id: "50%",
//         };

//         // Override default settings
//         listview.columns = listview.columns.map(column => {
//             if (custom_columns[column.fieldname]) {
//                 return {
//                     ...column,
//                     width: custom_columns[column.fieldname]
//                 };
//             }
//             return column;
//         });
//     }
// };

// frappe.listview_settings['Item'] = {
//     onload: function(listview) {
//         // Define custom widths for specific fields
//         const custom_columns = {
//             item_name: "200%", // Increase the width of the item_name column
//             id: "50%"          // Reduce the width of the id column
//         };

//         // Override default settings
//         listview.columns = listview.columns.map(column => {
//             if (custom_columns[column.fieldname]) {
//                 return {
//                     ...column,
//                     width: custom_columns[column.fieldname]
//                 };
//             }
//             return column;
//         });
//     }
// };


// frappe.listview_settings['Item'] = {
//     onload: function (listview) {
//         console.log('-------------------------')
//         // Wait for the list view to fully render
      
//             let itemNameColumn = listview.$result.find(`[data-fieldname="item_name"]`);
//             console.log(itemNameColumn)
//             if (itemNameColumn[0]) {
//                 itemNameColumn.css("width", "400%"); // Adjust width
//             }

//             // Find and adjust the column for `id`
//             let idColumn = listview.$result.find(`[data-fieldname="id"]`);
//             if (idColumn.length) {
//                 idColumn.css("width", "50%"); // Adjust width
//             }
      
//     }
// };




// frappe.listview_settings['Item'] = {
//     onload: function (listview) {
//         // Modify the list view column setup
//         listview.columns = listview.columns.map(column => {
//             if (column.fieldname === 'item_name') {
//                 column.width = '4 1 0'; // Flex settings: grow = 4, shrink = 1, basis = 0
//             } else if (column.fieldname === 'id') {
//                 column.width = '1 1 0'; // Flex settings: grow = 1, shrink = 1, basis = 0
//             } else {
//                 column.width = '2 1 0'; // Default flex settings for other columns
//             }
//             return column;
//         });

//         // Apply flex-based widths dynamically
//         listview.render_header = function () {
//             this.columns.forEach(column => {
//                 const th = this.header.find(`.list-row-head[data-fieldname="${column.fieldname}"]`);
//                 if (th) {
//                     const [grow, shrink, basis] = column.width.split(' ').map(Number);
//                     th.css({
//                         flexGrow: grow,
//                         flexShrink: shrink,
//                         flexBasis: basis + '%'
//                     });
//                 }
//             });
//         };
//     }
// };

// frappe.listview_settings['Item'] = {
//     onload: function (listview) {
//         // Apply custom inline CSS when the list view is loaded
//         listview.render_header = function () {
//             // Call the original render header function
//             frappe.views.ListView.prototype.render_header.call(this);

//             // Find the header for `item_name` and apply inline styles
//             const itemNameHeader = this.header.find('.list-row-head[data-fieldname="item_name"]');
//             if (itemNameHeader.length) {
//                 itemNameHeader.css({
//                     flex: '3', // Flex value for width adjustment
//                     justifyContent: 'start', // Align content to start
//                     overflow: 'hidden', // Handle overflow (optional)
//                     textOverflow: 'ellipsis', // Show ellipsis for long text (optional)
//                     whiteSpace: 'nowrap' // Prevent wrapping of text (optional)
//                 });
//             }
//         };
//     }
// };


// function extend_listview_event(doctype, event, callback) {
//     // if (!frappe.listview_settings[doctype]) {
//     //     frappe.listview_settings[doctype] = {};
//     // }

//     // const old_event = frappe.listview_settings[doctype][event];
//     // frappe.listview_settings[doctype][event] = function (listview) {
//     //     if (old_event) {
//     //         old_event(listview);
//     //     }
//     //     callback(listview);
//     // };
// }

// extend_listview_event("Item", "refresh", function (listview) {
//     const today = frappe.datetime.get_today();

//     listview.page.wrapper.find('.list-row').each(function() {
//         const $row = $(this);
//         const row_name = $row.find('[data-name]').data('name');
//         const row_data = listview.data.find(row => row.name === row_name);
        
//         if (row_data && row_data.posting_date === today) {
//             $row.css('background-color', 'lavender');
//         }
//     });
// });



//  Item list Width set Item name And Id Coloum
function extend_listview_event(doctype, event, callback) {
    if (!frappe.listview_settings[doctype]) {
        frappe.listview_settings[doctype] = {};
    }

    const old_event = frappe.listview_settings[doctype][event];
    frappe.listview_settings[doctype][event] = function (listview) {
        if (old_event) {
            old_event(listview);
        }
        callback(listview);
    };
}

extend_listview_event("Item", "refresh", function (listview) {
   

    // Set Item Name Width Using flex
    listview.page.wrapper.find('.list-subject').each(function () {
        const $subject = $(this);
        $subject.css({
            flex: '3.5', // Adjust the flex value
            justifyContent: 'start', // Align content to start
            overflow: 'hidden', // Optional: handle overflow
            textOverflow: 'ellipsis', // Optional: show ellipsis for long text
            whiteSpace: 'nowrap' // Optional: prevent wrapping
        });
    });

    // Set ID Width Using flex
    listview.page.wrapper.find('.list-row .level-right, .list-row-head .level-right').each(function () {
        const $subject = $(this);
        $subject.css({
            flex: '0.5', // Adjust the flex value
            justifyContent: 'start', // Align content to start
            
        });
    });
});
