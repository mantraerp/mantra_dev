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
	}
});