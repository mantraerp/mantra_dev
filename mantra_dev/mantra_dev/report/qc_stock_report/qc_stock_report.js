// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt


frappe.query_reports["QC Stock Report"] = {
    
    onload: function () {
        $(document).on("click", ".create_qc", function () {
            let item_code = $(this).data("item_code");
            let batch_no = $(this).data("batch_no");
            let stock_entry = $(this).data("stock_entry");
            let transfer_qty = parseFloat($(this).data("transfer_qty"));
            let actual_qty = parseFloat($(this).data("actual_qty"));
            
            frappe.model.with_doctype("Quality Inspection", function () {
                let qc = frappe.model.get_new_doc("Quality Inspection");
                qc.item_code=item_code
                qc.batch_no = batch_no
                qc.reference_type='Stock Entry'
                qc.reference_name = stock_entry
                qc.custom_actual_qty = actual_qty
                frappe.set_route("Form", "Quality Inspection", qc.name).then(() => {
                });
            });
        });
        
    },
};
