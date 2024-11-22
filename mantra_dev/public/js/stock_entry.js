frappe.ui.form.on('Stock Entry', {
	refresh(frm) {
	    var mr_no = frm.doc.custom_material_request_no;
	    if(mr_no && frm.doc.add_to_transit === 1){
	        frappe.call({
			method: "mantra_dev.backend_code.api.warehouse_manager_data_fetch_stock_entry",
			args: {
				"mr_no": mr_no,
			},
		}).then(r => {
 			// fetching the data from the db
			var warehouse_data = r.message;
            var wm = warehouse_data.flat();
            console.log(wm);
			currentuser = frappe.session.user;
			
            var index = wm.indexOf(currentuser);
            console.log(index);
            if (index == -1) {
                console.log("111");
                wm.splice(index, 1);
                wm.unshift(currentuser);
                // wm.forEach(function(obj) {
                for (var i = 0; i < wm.length; i++) {
                    // if (obj.warehouse_manager !== currentuser) {
                    if (wm[i] == currentuser) {
                        console.log("1");
                        { setTimeout(() => {
                            frm.remove_custom_button("End Transit");
                        }, 0); }
                        break; 
                    }
                }
            }
            // });
            
		});
	    }
	},
    	
	before_save: function(frm) {

        if (frm.doc.stock_entry_type=="QC Transfer") 
        {
            frm.doc.items.forEach((row) => {

                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Item",
                        fieldname: ["custom_inspection_required_before_transfer_warehouse", "item_name"],
                        filters: {
                            name: row.item_code
                        },
                    },
                    callback: function (r) 
                    {
                        var inspection_require = r.message.custom_inspection_required_before_transfer_warehouse;
                        if (inspection_require) {
                            item.custom_inspection_required_before_transfer_warehouse = inspection_require;
                        }
                        else {
                            item.custom_inspection_required_before_transfer_warehouse = 0;
                        }
                    },
                });

                
                frm.set_query("quality_inspection", "items", function(doc, cdt, cdn) 
                {
                    return {
                            "filters": [
                                ["Quality Inspection", "item_code", "=", row.item_code],
                            ]
                        }
                });

                frappe.db.get_value("Quality Inspection", {"name": row.quality_inspection}, ["item_code","sample_size"], function(value) 
                {

                    if(value.item_code!=row.item_code)
                    {
                        frappe.throw(__(item.item_name.concat(" ( ", row.item_code, " )"," is not match in inspection report ",row.quality_inspection," .")));
                        row.quality_inspection = "";
                        return false;
                    }
                    
                    if(value.sample_size!=row.qty)
                    {
                        frappe.throw(__(item.item_name.concat(" ( ", row.item_code, " )"," quantity is not match in inspection report ",row.quality_inspection," .")));
                        row.quality_inspection = "";
                        return false;
                    }
                });
            });
        }
    },
    before_submit: function(frm) {

        if (frm.doc.stock_entry_type=="QC Transfer") 
        {
            // If any how defaul source is change by user
            if (frm.doc.from_warehouse!="QC Remain - MSIPL") 
            {
                msgprint('QC Transfer require default source warehouse as QC Remain - MSIPL.');
                return false;
            }

            frm.doc.items.forEach((item) => {
                 if(item.custom_inspection_required_before_transfer_warehouse==1)
                {
                     if(!item.quality_inspection)
                     {
                        frappe.throw(__(item.item_name.concat(" ( ", item.item_code, " )"," inspection is require before transfer.")));
                        return false;
                     }
                     else
                     {
                        frappe.db.get_value("Quality Inspection", {"name": item.quality_inspection}, "status", function(value) 
                        {
                            if(value.status=="Accepted")
                            {
                                item.t_warehouse=frm.doc.to_warehouse;
                            }
                            else
                            {
                                item.t_warehouse="Rejected Warehouse - MSIPL";
                            }
                        });
                     }
                }
            });  
            
            
            
            frm.doc.items.forEach((item) => {
             
                if(item.custom_inspection_required_before_transfer_warehouse==0)
                {
                    frappe.call({
                        method: "frappe.client.get_value",
                        args: {
                            doctype: "Item",
                            fieldname: ["custom_inspection_required_before_transfer_warehouse", "item_name"],
                            filters: {
                                name: item.item_code
                            },
                        },
                        callback: function (r) 
                        {
                            var inspection_require = r.message.custom_inspection_required_before_transfer_warehouse;
                            if (inspection_require) 
                            {
                                if(!item.quality_inspection)
                                {
                                    frappe.throw(__(item.item_name.concat(" ( ", item.item_code, " )"," inspection is require before transfer.")));
                                    item.t_warehouse="Rejected Warehouse - MSIPL";
                                    return false;
                                }
                                else
                                {
                                    frappe.db.get_value("Quality Inspection", {"name": item.quality_inspection}, "status", function(value) 
                                    {
                                        if(value.status=="Accepted")
                                        {
                                            item.t_warehouse=frm.doc.to_warehouse;
                                        }
                                        else
                                        {
                                            item.t_warehouse="Rejected Warehouse - MSIPL";
                                        }
                                    });
                                }
                            }
                        },
                    });
                }
            });
        }
    }
});

frappe.ui.form.on('Stock Entry Detail', {
    // cdt is Child DocType name i.e Quotation Item
    // cdn is the row name for e.g bbfcb8da6a
    item_code(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (frm.doc.__unsaved && frm.doc.stock_entry_type=="QC Transfer" && row.s_warehouse!="QC Remain - MSIPL") {
            alert("QC Transfer require source warehouse as 'QC Remain - MSIPL'.");
            row.item_code = "";
        }
    },
    quality_inspection(frm, cdt, cdn) {

        let row = frappe.get_doc(cdt, cdn);


        if(!row.quality_inspection)
        {
            row.quality_inspection = "";
            return false;
        }


        frm.set_query("quality_inspection", "items", function(frm, cdt, cdn) 
        {
            return {
                    "filters": [
                        ["Quality Inspection", "item_code", "=", row.item_code],
                    ]
                }
        });


        frappe.db.get_value("Quality Inspection", {"name": row.quality_inspection}, ["item_code","sample_size"], function(value) 
        {

            if(value.item_code!=row.item_code)
            {
                msgprint((row.item_name.concat(" ( ", row.item_code, " )"," is not match in inspection report ",row.quality_inspection," item.")));
                // frappe.throw(__(row.item_name.concat(" ( ", row.item_code, " )"," is not match in inspection report ",row.quality_inspection," .")));
                row.quality_inspection = "";
                return false;
            }
            
            if(value.sample_size!=row.qty)
            {
                // frappe.throw(__(item.item_name.concat(" ( ", row.item_code, " )"," quantity is not match in inspection report ",row.quality_inspection," .")));
                msgprint((row.item_name.concat(" ( ", row.item_code, " )"," quantity is not match in inspection report ",row.quality_inspection," item sample size.")));

                row.quality_inspection = "";
                return false;
            }
        });
    }
});