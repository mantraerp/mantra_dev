// frappe.ui.form.on('Subcontracting Receipt', {
//     onload(frm) {
//         frm.set_query('set_warehouse', () => {
//             return {
//                 filters: {
//                     custom_is_purchase_warehouse: 1
//                 }
//             };
//         });
//         frm.set_query('rejected_warehouse', () => {
//             return {
//                 filters: {
//                     custom_is_purchase_warehouse: 1
//                 }
//             };
//         });
//         frm.set_query('supplier_warehouse', () => {
//             return {
//                 filters: {
//                     custom_is_subcontracting_warehouse: 1
//                 }
//             };
//         });
//     }
// });