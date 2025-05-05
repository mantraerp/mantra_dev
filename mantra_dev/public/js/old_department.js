


// frappe.ui.form.on("Department", {
//     onload: function (frm) {
//         frm.previous_warehouse = (frm.doc.custom_departmental_warehouse || []).map(row => row.warehouse);
//         frm.previous_stock_entry_type = (frm.doc.custom_departmental_stock_entry_type || []).map(row => row.stock_entry_type);

//     },

//     before_save: function (frm) {
//         let current_items = (frm.doc.custom_departmental_warehouse || []).map(row => row.warehouse);

//         let removed_warehouse = frm.previous_warehouse.filter(warehouse => !current_items.includes(warehouse));
//         let added_warehouse = current_items.filter(warehouse => !frm.previous_warehouse.includes(warehouse));




//         let current_stock_entry_type = (frm.doc.custom_departmental_stock_entry_type || []).map(row => row.stock_entry_type);

//         let removed_stock_entry_type = frm.previous_stock_entry_type.filter(stock_entry_type => !current_stock_entry_type.includes(stock_entry_type));
//         let added_stock_entry_type = current_stock_entry_type.filter(stock_entry_type => !frm.previous_stock_entry_type.includes(stock_entry_type));
//         console.log(added_stock_entry_type)

       

//         if (removed_warehouse.length > 0 || added_warehouse.length > 0) {
//             frappe.call({
//                 method: "mantra_dev.backend_code.department.department.handle_warehouse_changes",
//                 args: {
//                     added_warehouse: JSON.stringify(added_warehouse),  // Convert to JSON string
//                     removed_warehouse: JSON.stringify(removed_warehouse),
//                     doc_name:JSON.stringify(frm.doc.name)
//                 },
//                 callback: function(response) {
//                     if (response.message) {

//                         if (response.message.removed_warehouse) {
//                         }
//                         if (response.message.added_warehouse) {
//                         }
//                     } else {
//                     }
//                 }
//             });
//         }

//         if (removed_stock_entry_type.length > 0 || added_stock_entry_type.length > 0) {
//             frappe.call({
//                 method: "mantra_dev.backend_code.department.department.handle_stock_entry_type_changes",
//                 args: {
//                     added_stock_entry_type: JSON.stringify(added_stock_entry_type),  // Convert to JSON string
                    
//                     removed_stock_entry_type: JSON.stringify(removed_stock_entry_type),
//                     doc_name:JSON.stringify(frm.doc.name)
//                 },
                
//                 callback: function(response) {
//                     if (response.message) {

//                         if (response.message.removed_warehouse) {
//                         }
//                         if (response.message.added_warehouse) {
//                         }
//                     } else {
//                     }
//                 }
//             });
//         }


//         frm.previous_warehouse = [...current_items];
//         frm.previous_stock_entry_type = [...current_stock_entry_type];
//     },

    

// });





// frappe.ui.form.on('Material Request Type Purpose', {
//     material_request_type: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         console.log(row.parent)

//         // Ensure department exists before making a request
//         if (row.material_request_type) {
//             frappe.call({
//                 method: "mantra_dev.backend_code.department.department.material_request_type_list",
//                 args: {
//                     department: row.parent,
//                     purpose:row.material_request_type
//                 },
//                 // console.log(row.parent);
//                 callback: function(response) {
//                     if (response.message) {
//                         console.log("Fetched Departmental Permission Records:", response.message);
//                         frappe.msgprint(__("Departmental Permission records fetched. Check console."));
//                     }
//                 }
//             });
//         }
//     },
//     before_custom_material_request_type_remove: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         console.log(row.parent)

//         frappe.call({
//             method: "mantra_dev.backend_code.department.department.remove_material_request_type",
//             args: {
//                 department: row.parent,
//                 purpose: row.material_request_type
//             },
//             callback: function(response) {
//                 if (response.message) {
//                     console.log("Removed Departmental Permission Record:", response.message);
//                     frappe.msgprint(__("Departmental Permission record removed."));
//                 }
//             }
//         });
//     }
    
// });


