// Copyright (c) 2024, Foram Shah and contributors
// For license information, please see license.txt

frappe.ui.form.on("Serial No Reconciliation", {
    // Fetch given serial no data if it is linked with particular Item code
    get_data(frm) {
        if (frm.is_new()) {
            frappe.throw("Please Save the document first...");
        } else {
            if (frm.is_dirty()) {
                frappe.throw("Please save changes before proceeding...");
            } else {
                frappe.call({
                    method: "mantra_dev.mantra_dev.doctype.serial_no_reconciliation.serial_no_reconciliation.get_serial_no",
                    args: {
                        doc_name: frm.doc.name,
                    },
                    callback: function (r) {
                        if (r.message) {

                            if (r.message.non_matching_serials) {
                                frm.set_value("non_matching_serial_no", "");
                                frm.set_value("non_matching_serial_no", r.message.non_matching_serials);
                                frm.save();
                            }
                            else {
                                frm.set_value("non_matching_serial_no", "");
                                frm.save();
                            }

                            if (r.message.matching_serials) {
                                frm.clear_table("item_serial_no");
                                r.message.matching_serials.forEach(serial => {
                                    let row = frm.add_child("item_serial_no");
                                    row.serial_no = serial.serial_no;
                                    row.item_code = serial.item_code;
                                    row.warehouse = serial.warehouse;
                                    row.status = serial.status;
                                });

                                frm.refresh_field("item_serial_no");
                                frm.save();
                                frappe.show_alert({ message: "Serial numbers updated successfully!", indicator: "green" });
                            }
                            else {
                                frm.refresh_field("item_serial_no");
                                frm.save();
                            }
                        }
                    }
                });
            }
        }
    },

    refresh(frm) {
        // Add Reconcile button in listview of child table
        frm.fields_dict["item_serial_no"].$wrapper.find('.grid-body .rows').find(".grid-row").each(function (i, item) {
            let field = $(item).find('[data-fieldname="reconcile"]');
            field.empty(); 
        
            let container = $('<div class="reconcile-btn-container"></div>').css({
                // position: "relative",
                display: "flex",
                justifyContent: "center",  
                alignItems: "center",     
                // width: "100%",
                height: "100%",
            });
        
            let button = $("<button class='btn btn-xs btn-success'>Reconcile</button>").css({
                // minWidth: "70px",       
                // padding: "5px",         
                // boxSizing: "border-box",
                // textAlign: "center"
            });
        
            container.append(button);
            field.append(container);
        
            button.click(function (event) {
                event.preventDefault();   

                let cdn = $(item).attr('data-name');
                let cdt = frm.fields_dict["item_serial_no"].grid.doctype;

                reconcile_serial_no(frm, cdt, cdn);
            });
        });
        
    },

    warehouse(frm) {
        if (frm.is_dirty()) {
            frm.clear_table("item_serial_no");
            frm.refresh_field("item_serial_no");
        }
    },

    item_code(frm) {
        if (frm.is_dirty()) {
            frm.clear_table("item_serial_no");
            frm.refresh_field("item_serial_no");
        }
    },

    serial_no(frm) {
        if (frm.is_dirty()) {
            frm.clear_table("item_serial_no");
            frm.refresh_field("item_serial_no");
        }
    },

});

frappe.ui.form.on("Item Serial No", {

    reconcile(frm, cdt, cdn) {
        reconcile_serial_no(frm, cdt, cdn);
    }
});

// Reconcile serial no with given warehouse if serial no is active
function reconcile_serial_no(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);

    if (frm.doc.warehouse === row.warehouse && row.status === "Active") {
        frappe.throw(`Serial No ${row.serial_no} is already in Warehouse: ${row.warehouse}`);
    } else if (frm.doc.warehouse !== row.warehouse && row.status === "Active") {
        frappe.call({
            method: "mantra_dev.mantra_dev.doctype.serial_no_reconciliation.serial_no_reconciliation.update_serial_no_warehouse",
            args: {
                serial_no: row.serial_no,
                item_code: row.item_code,
                warehouse: frm.doc.warehouse
            },
            callback: function (r) {
                if (r.message === "success") {
                    frappe.show_alert({ message: `Warehouse updated for Serial No: ${row.serial_no}`, indicator: "green" });
                    row.warehouse = frm.doc.warehouse;
                    frm.refresh_field("item_serial_no");
                }
            }
        });
    } else {
        frappe.throw(`Serial No ${row.serial_no} is either inactive or not valid for reconciliation.`);
    }
}