// Item list Width set Item name And Id Coloum
frappe.listview_settings['Item'] = {
    refresh: function (listview) {
        $(".layout-side-section").hide();
    
      },
    onload: function (listview) {
        // Add custom styles dynamically
        const style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = `
            .list-row .level-left, .list-row-head .level-left{
                min-width: 90% !important;
            }
            .list-row-col:last-child {
                flex: 1 !important;
            }
            .list-row-col {
                flex: 3 !important;
                margin-right: 15px;
            }
            .list-subject {
                flex: 6 !important;
            }
        `;
        document.head.appendChild(style);
    }
};