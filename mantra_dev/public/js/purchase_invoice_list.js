
frappe.listview_settings["Purchase Invoice"].onload = function (listview) {
		




        if (frappe.session.user !== "Administrator") {
            frappe.call({
                method: "mantra_dev.backend_code.api.get_user_purchase_invoice",
                args: {
                    user: frappe.session.user
                },
                async: false, // Ensure this runs before the list loads
                callback: function (r) {
                    let allowed_docnames = (r.message && r.message.length > 0) ? r.message : ["NoData"];
                    
                    // Set route options to apply filters before list loads
                    frappe.route_options = {
                        "name": ["in", allowed_docnames]
                    };

                    // Reload the page to apply the filters immediately before list fetch
                    frappe.set_route("List", "Purchase Invoice");
                }
            });
        } else {
            console.log("Session user is Administrator, showing all documents...");
        }
};
