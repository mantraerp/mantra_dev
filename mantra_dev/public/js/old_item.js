frappe.ui.form.on('Item', {
    
  onload(frm) {
        let dropdown;
        let activeIndex = -1;

        // Attach input event on item_name field
        frm.fields_dict.item_name.$input.on("input", function (e) {
            let search_term = $(this).val();
            activeIndex = -1;

            if (search_term.length > 0) {
                console.log(search_term);
                frappe.call({
                    method: "mantra_dev.backend_code.api.search_item_names",
                    args: {
                        search_term: search_term
                    },
                    callback: function (r) {
                        if (r.message) {
                            let suggestions = r.message;

                            // Remove previous dropdown
                            $(".custom-dropdown").remove();

                            if (suggestions.length > 0) {
                                dropdown = $("<ul class='dropdown-menu custom-dropdown' style='display: block; position: absolute; z-index: 1000;'></ul>");

                                suggestions.forEach((item_name) => {
                                    let list_item = $("<li class='dropdown-item'></li>").text(item_name);

                                    list_item.on("click", function () {
                                        frm.set_value("item_name", item_name);
                                        $(".custom-dropdown").remove();
                                    });

                                    dropdown.append(list_item);
                                });

                                frm.fields_dict.item_name.$wrapper.append(dropdown);
                            }
                        }
                    }
                });
            } else {
                $(".custom-dropdown").remove();
            }
        });

        // Keyboard navigation
        frm.fields_dict.item_name.$input.on("keydown", function (e) {
            if (dropdown) {
                let items = dropdown.find(".dropdown-item");
                if (e.key === "ArrowDown") {
                    e.preventDefault();
                    activeIndex = (activeIndex + 1) % items.length;
                    updateActive(items);
                } else if (e.key === "ArrowUp") {
                    e.preventDefault();
                    activeIndex = (activeIndex - 1 + items.length) % items.length;
                    updateActive(items);
                } else if (e.key === "Enter") {
                    e.preventDefault();
                    if (activeIndex > -1) {
                        let selectedValue = $(items[activeIndex]).text();
                        frm.set_value("item_name", selectedValue);
                        $(".custom-dropdown").remove();
                    }
                }
            }
        });

        // Remove dropdown on outside click
        $(document).on("click", function () {
            $(".custom-dropdown").remove();
        });

        function updateActive(items) {
            items.removeClass("active");
            if (activeIndex > -1) {
                $(items[activeIndex]).addClass("active");
            }
        }

        frm.add_custom_button(("Used as Raw Material in BOM"), () => {
            frappe.call({
                method: "mantra_dev.backend_code.item.item.fetch_item_used_as_raw_material_in_bom",
                args: { item_code: frm.doc.name },
                callback: function (r) {
                    if (r.message.length > 0){
                        var data_list = r.message;
                        var d = new frappe.ui.Dialog({
                            title: __("Used as Raw Material in BOM"),
                            size: "large",
                            fields: [
                                {
                                    "fieldname": "bom_details",
                                    "fieldtype": "Table",
                                    "label": "Item Details",
                                    "cannot_add_rows": 1,
                                    "cannot_delete_rows": 1,
                                    "fields": [
                                        {
                                            "fieldname": "item_code",
                                            "fieldtype": "Link",
                                            "label": "Item Code",
                                            "options": "Item",
                                            "read_only": 1,
                                            "in_list_view": 1,
                                            "columns": 5
                                        },
                                        {
                                            "fieldname": "bom",
                                            "fieldtype": "Link",
                                            "label": "BOM",
                                            "options": "BOM",
                                            "read_only": 1,
                                            "in_list_view": 1,
                                            "columns": 2
                                        },
                                        {
                                            "fieldname": "qty",
                                            "fieldtype": "Float",
                                            "label": "Qty Used",
                                            "read_only": 1,
                                            "in_list_view": 1,
                                            "columns": 1
                                        },
                                        {
                                            "fieldname": "uom",
                                            "fieldtype": "Link",
                                            "options": "UOM",
                                            "label": "UOM",
                                            "read_only": 1,
                                            "in_list_view": 1,
                                            "columns": 1
                                        },
                                        {
                                            "fieldname": "is_default_bom",
                                            "fieldtype": "Check",
                                            "label": "Is Default BOM",
                                            "read_only": 1,
                                            "in_list_view": 1,
                                            "columns": 1
                                        },
                                    ],
                                    "data": data_list
                                }
                            ]
                        })
                        d.show();
                    }else{
                        frappe.msgprint("This item has not been used in any BOM")
                    }
                }
            })
        },('Utility'))
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