// Copyright (c) 2025, Foram Shah and contributors
// For license information, please see license.txt

frappe.ui.form.on("PO Form Approval", {
    purchase_order(frm){
        // Fetch Details of Some Field Based On Purchase Order and Update Default Fields List
        frappe.call({
            method: 'mantra_dev.mantra_dev.doctype.po_form_approval.po_form_approval.get_purchase_order_against_details',
            args:{
                'purchase_order_id': frm.doc.purchase_order
            },
            callback: function(r) {
                let default_fields = ['sales_order', 'material_request', 'requester', 'cost_center', 'business_unit_name', 'business_unit_email', 'purpose', 'approved_by'];
                if (r.message) {
                    default_fields.forEach(field => {
                        frm.set_value(field, r.message[field]);
                        frm.refresh_field(field);
                    });
                } else {
                    default_fields.forEach(field => {
                        frm.set_value(field, '');
                        frm.refresh_field(field);
                    });
                    
                }
            }
        })
    },
    onload(frm){
        if (frm.doc.purchase_order && frm.is_new()){
            frm.events.purchase_order(frm);
            frm.events.supplier(frm);
        }
    },
	supplier(frm) {
        // Supplier NDA Fetch From Supplier Master
        frm.set_value('nda', '')
        frm.refresh_field('nda')
        if (frm.doc.supplier){
            frappe.call({
                method: 'mantra_dev.mantra_dev.doctype.po_form_approval.po_form_approval.get_supplier_nda',
                args:{
                    'supplier_id': frm.doc.supplier
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('nda', r.message)
                        frm.refresh_field('nda')   
                    }
                }
            })
        }
	},
});


frappe.ui.form.on("PO Form Price Comparison", {
    // On Row Add or Delete Based On Comment Field Reqd Change
    price_comparison_add(frm){
        frm.toggle_reqd('comment', frm.doc.price_comparison.length > 1);
    },
    price_comparison_remove(frm) {
        frm.toggle_reqd('comment', frm.doc.price_comparison.length > 1);
    }
})