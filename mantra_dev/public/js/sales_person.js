
// frappe.ui.form.on("Sales Person", {
// refresh:function(frm){
// },
// custom_product: function (frm) {
//     frm.set_value("custom_items", []);

//     let selected_products = frm.doc.custom_product || [];
    

//     if (selected_products.length > 0) {
//         frappe.call({
//             method: "mantra_dev.mantra_dev.doctype.departmental_permission.departmental_permission.get_items_for_products",
//             args: {
//                 selected_products:frm.doc.custom_product
//             },
//             callback: function (r) {
//                 if (r.message) {
                   

//                     r.message.forEach(element => {
//                         let itemExists = frm.doc.custom_items.some(row => row.item === element);
//                         if (!itemExists) {
//                         frm.add_child('custom_items',{
//                             'item':element

//                         })
//                     }
//                     });
//                     frm.refresh_field('custom_items');
//                 }
//             }
//         });
//     }
// },
// custom_items: function (frm) {
   


//     let selected_products = frm.doc.custom_items || [];

//     if (selected_products.length > 0) {
//         let last_item = selected_products[selected_products.length - 1]; // Get the last item
//         console.log("Last Selected Item:", last_item.item);
//     }


// }


// });