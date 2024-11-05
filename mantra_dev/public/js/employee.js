frappe.ui.form.on('Employee', {
	department(frm) {
	    frm.set_value("custom_opration_approver",undefined)
	    frappe.call({
	        method:"mantra_dev.backend_code.api.get_opration_approver",
	        args:
	        {
	           department :cur_frm.doc.department,
	        },
	       callback: function(r) {
	            // alert(r.message)
	            // if (r.message.length!=0){
	                setTimeout(() => {
                        frm.set_query('custom_opration_approver', () => {
                            return {
                                filters: {
                                    name: ["in",r.message]
                                }
                            };
                        });
                    }, 1000); // 
    // },
	            // }	            
	       }	        
	    })
	}
})