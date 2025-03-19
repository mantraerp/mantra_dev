// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Departmental Permission", {
// 	refresh(frm) {

// 	},
// });





// frappe.ui.form.on("Departmental Permission", {

   
//     refresh:function(frm){
//         console.log("frm")
//     },
//     product: function (frm) {
//         frm.set_value("items", []);

//         let selected_products = frm.doc.product || [];
        
//         console.log(selected_products)

//         if (selected_products.length > 0) {
//             frappe.call({
//                 method: "mantra_dev.mantra_dev.doctype.departmental_permission.departmental_permission.get_items_for_products",
//                 args: {
//                     selected_products:frm.doc.product
//                 },
//                 callback: function (r) {
//                     if (r.message) {
                       

//                         r.message.forEach(element => {
//                             let itemExists = frm.doc.items.some(row => row.item === element);
//                             if (!itemExists) {
//                             frm.add_child('items',{
//                                 'item':element

//                             })
//                         }
//                         });
//                         frm.refresh_field('items');
                       
//                     }
//                 }
//             });
//         }
//     },
//     items: function (frm) {
       


//         let selected_products = frm.doc.items || [];

//         if (selected_products.length > 0) {
//             let last_item = selected_products[selected_products.length - 1]; // Get the last item
            
//         }


        
//     }
    

// });
















