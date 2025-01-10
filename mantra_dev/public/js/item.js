frappe.ui.form.on('Item', {
    
  onload(frm) {   
        // Attach autocomplete functionality to the item_name field
        let dropdown;
        let activeIndex = -1; // Track the currently active suggestion

        frm.fields_dict.item_name.$input.on("input", function (e) {
            let search_term = $(this).val();
            activeIndex = -1; // Reset active index when user types

            if (search_term.length > 0) {
                // Remove non-alphanumeric characters from the search term
                let sanitized_search_term = search_term.replace(/[^a-zA-Z0-9]/g, '');

                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Item",
                        fields: ["item_name"],
                        // filters: [["item_name", "like", `%${search_term}%`]], // Keep special characters for database query
                        // filters: [["disabled", "=", 1]], // Keep special characters for database query
                        limit_page_length: 20 // Retrieve more results for better filtering
                    },
                    callback: function (r) {
                        if (r.message) {
                            // Preprocess item names to remove non-alphanumeric characters and filter results
                            let suggestions = r.message.filter(item => {
                                let sanitized_item_name = item.item_name.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
                                return sanitized_item_name.includes(sanitized_search_term.toLowerCase());
                            }).map(item => item.item_name);

                            // If there are suggestions, create a dropdown
                            if (suggestions.length > 0) {
                                dropdown = $("<ul class='dropdown-menu' style='display: block; position: absolute;'></ul>");
                                suggestions.forEach((item_name, index) => {
                                    let list_item = $("<li class='dropdown-item'></li>").text(item_name);

                                    // Handle click selection
                                    list_item.on("click", function () {
                                        frm.set_value("item_name", item_name); // Set selected value
                                        dropdown.remove(); // Remove dropdown
                                    });

                                    dropdown.append(list_item);
                                });

                                // Remove existing dropdown if present
                                $(".dropdown-menu").remove();

                                // Attach dropdown to the field
                                frm.fields_dict.item_name.$wrapper.append(dropdown);
                            } else {
                                $(".dropdown-menu").remove(); // Remove dropdown if no suggestions
                            }
                        }
                    }
                });
            } else {
                // Remove dropdown if input is empty
                $(".dropdown-menu").remove();
            }
        });

        // Handle keydown events for navigation
        frm.fields_dict.item_name.$input.on("keydown", function (e) {
            if (dropdown) {
                let items = dropdown.find(".dropdown-item");
                if (e.key === "ArrowDown") {
                    // Move down in the list
                    e.preventDefault();
                    activeIndex = (activeIndex + 1) % items.length;
                    updateActive(items);
                } else if (e.key === "ArrowUp") {
                    // Move up in the list
                    e.preventDefault();
                    activeIndex = (activeIndex - 1 + items.length) % items.length;
                    updateActive(items);
                } else if (e.key === "Enter") {
                    // Select the active suggestion
                    e.preventDefault();
                    if (activeIndex > -1) {
                        let selectedValue = $(items[activeIndex]).text();
                        frm.set_value("item_name", selectedValue); // Set selected value
                        dropdown.remove(); // Remove dropdown
                    }
                }
            }
        });

        // Helper function to update the active item
        function updateActive(items) {
            items.removeClass("active");
            if (activeIndex > -1) {
                $(items[activeIndex]).addClass("active");
            }
        }

        // Remove dropdown if the user clicks outside
        $(document).on("click", function () {
            $(".dropdown-menu").remove();
        });
    },


    // item_group(frm) {
    //     if (cur_frm.doc.item_group == "Services") {
    //         frm.set_value("is_stock_item", 0)
    //         cur_frm.set_df_property("is_stock_item", "read_only", 1)
    //     }
    // },
    // before_save(frm) {
    //     if (cur_frm.doc.item_group == "Services") {
    //         frm.set_value("is_stock_item", 0)
    //         cur_frm.set_df_property("is_stock_item", "read_only", 1)
    //     }
    // }
})