// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Product", {
// 	refresh(frm) {

// 	},
// });






// frappe.ui.form.on('Product Item', {

//     item_code: function (frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
    
//         if (row.item_code) {
//             console.log("Selected Item Code:", row.item_code); // Correct way to log in JS
    
//             frappe.call({
//                 method: "mantra_dev.mantra_dev.doctype.product.product.product_change_events_add",
//                 args: {
//                     item_code: row.item_code,
//                     name: frm.doc.name
//                 },
//                 callback: function (response) {
//                     if (response.message) {
//                         frappe.msgprint(__('Item Permission updated.'));
//                     }
//                 }
//             });
//         }
//     },
    
   

//     before_items_remove: function (frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
        
//         if (row && row.item_code) {
//             console.log("Removing Item Code:", row.item_code);

//             frappe.call({
//                 method: "mantra_dev.mantra_dev.doctype.product.product.product_change_events",
//                 args: {
//                     item_code: row.item_code,
//                     name: frm.doc.name
//                 },
//                 callback: function (response) {
//                     if (response.message) {
//                         frappe.msgprint(__('Item Permission updated.'));
//                     }
//                 }
//             });
//         }
//     },
    


// });





// frappe.ui.form.on("Product", {
//     onload: function (frm) {
//         frm.previous_department = (frm.doc.product_department || []).map(row => row.department);
        
//     },

//     before_save: function (frm) {
//         let current_department= (frm.doc.product_department || []).map(row => row.department);

//         let removed_department = frm.previous_department.filter(department => !current_department.includes(department));
//         let added_department = current_department.filter(department => !frm.previous_department.includes(department));
//         console.log("Remove department",removed_department)
//         console.log("added department",added_department)



        

//         if (removed_department.length > 0 || added_department.length > 0) {
//             frappe.call({
//                 method: "mantra_dev.mantra_dev.doctype.product.product.department_remove_and_add",
//                 args: {
//                     added_department: JSON.stringify(added_department),  
//                     removed_department: JSON.stringify(removed_department),
//                     doc_name:JSON.stringify(frm.doc.name),
//                     doc_items:JSON.stringify(frm.doc.items)
//                 },
//                 callback: function(response) {
//                     if (response.message) {

//                         if (response.message.removed_department) {
//                         }
//                         if (response.message.added_department) {
//                         }
//                     } else {
//                     }
//                 }
//             });
//         }

       
//         frm.previous_department = [...current_department]
//     },
// });