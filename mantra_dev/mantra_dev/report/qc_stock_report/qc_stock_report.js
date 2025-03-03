// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt


frappe.query_reports["QC Stock Report"] = {
    "filters": [
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "MultiSelectList",
            "options": [],
            "reqd": 0,
            "get_data": function(txt) {
                return new Promise((resolve) => {
                    frappe.call({
                        method: "mantra_dev.mantra_dev.report.qc_stock_report.qc_stock_report.get_qc_warehouses",
                        callback: function(response) {
                            let options = response.message;
                            console.log(options);
                            resolve(options);
                        }
                    });
                });
            }
        }
    ],
    onload: function () {
        $(document).on("click", ".create_qc", function () {
            let item_code = $(this).data("item_code");
            let batch_no = $(this).data("batch_no");
            let stock_entry = $(this).data("stock_entry");
            let transfer_qty = parseFloat($(this).data("transfer_qty"));
        
            frappe.model.with_doctype("Quality Inspection", function () {
                let qc = frappe.model.get_new_doc("Quality Inspection");
                qc.item_code=item_code
                qc.batch_no = batch_no
                qc.reference_type='Stock Entry'
                qc.reference_name = stock_entry
                qc.custom_actual_qty = transfer_qty
                frappe.set_route("Form", "Quality Inspection", qc.name).then(() => {
                });
            });
        });
        
    },
};

// // Redirect function for Create QC button
// window.redirectToQCForm = function(item_code, batch_no, purchase_receipt, transfer_qty) {
//     console.log(parseFloat(transfer_qty));
    
//     frappe.route_options = {
//         'item_code': item_code,
//         'batch_no': batch_no,
//         'reference_type' : "Purchase Receipt",
//         'reference_name' : purchase_receipt,
//         'custom_actual_qty' : parseFloat(transfer_qty)
//     }
//     // frappe.set_route('quality-inspection', 'new');
//     frappe.set_route('Form', 'Quality Inspection', 'new').then(() => {
//         setTimeout(() => {
//             cur_frm.set_value('custom_actual_qty', parseFloat(transfer_qty));
//         }, 500); // Short delay to ensure the form is loaded
//     });
    
// };
