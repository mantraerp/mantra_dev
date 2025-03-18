import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from collections import defaultdict
from erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle import get_auto_batch_nos
from mantra_dev.backend_code.globle import create_notification_log


@frappe.whitelist()
def get_auto_transfer_stock():
    """Fetch the 'auto_transfer_stock_for_non_qc_items' value from QC Settings."""

    return frappe.db.get_value("QC Settings", "QC Settings", "auto_transfer_stock_for_non_qc_items")


@frappe.whitelist()
# If auto_transfer_stock_for_non_qc_items is 1, create a stock entry for all items which do not required QC
def create_stock_entry_for_auto_transfer_stock(purchase_receipt):
    try:
        # Fetch items that do not require QC
        receipt_items = frappe.get_all(
            "Purchase Receipt Item",
            filters={"parent": purchase_receipt, "custom_inspection_required_before_transfer_warehouse": 0},
            fields=["item_code", "warehouse", "batch_no", "serial_no", "serial_and_batch_bundle", "qty"]
        )

        if not receipt_items:
            return _("No items found for auto stock transfer.")

        # Fetch default QC accepted warehouse
        qc_settings = frappe.get_single("QC Settings")
        target_warehouse = qc_settings.default_qc_accepted_warehouse

        if not target_warehouse:
            frappe.throw(_("Default QC Accepted Warehouse is not set in QC Settings."))

        def fetch_serial_and_batch(item):
            """Fetch serial and batch numbers from the Serial and Batch Bundle if not directly present."""
            serial_no_str = item.get("serial_no")
            batch_no = item.get("batch_no")
            bundle_name = item.get("serial_and_batch_bundle")

            if not serial_no_str and not batch_no and bundle_name:
                bundle_details = frappe.get_all(
                    "Serial and Batch Entry",
                    filters={"parent": bundle_name},
                    fields=["serial_no", "batch_no"]
                )

                batch_numbers = list(set(d["batch_no"] for d in bundle_details if d["batch_no"]))
                serial_numbers = [d["serial_no"] for d in bundle_details if d["serial_no"]]

                if batch_numbers:
                    batch_no = batch_numbers[0]  # Pick the first batch if multiple exist
                if serial_numbers:
                    serial_no_str = "\n".join(serial_numbers)

            return serial_no_str, batch_no

        def map_item(source, target, source_parent):
            target.reference_purchase_receipt = purchase_receipt
            target.s_warehouse = source.warehouse
            target.t_warehouse = target_warehouse
            target.qty = source.qty

            # Get serial and batch numbers
            serial_no_str, batch_no = fetch_serial_and_batch(source)

            target.use_serial_batch_fields = 1 if serial_no_str or batch_no else 0
            if serial_no_str:
                target.serial_no = serial_no_str  
            if batch_no:
                target.batch_no = batch_no

        stock_entry = get_mapped_doc(
            "Purchase Receipt",
            purchase_receipt,
            {
                "Purchase Receipt": {
                    "doctype": "Stock Entry",
                    "field_map": {},
                },
                "Purchase Receipt Item": {
                    "doctype": "Stock Entry Detail",
                    "field_map": {},
                    "postprocess": map_item, 
                    "condition": lambda doc: doc.custom_inspection_required_before_transfer_warehouse == 0 
                },
            },
            target_doc=None
        )

        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.purchase_receipt_no = purchase_receipt
        stock_entry.custom_from_qc = 1  

        # Insert and submit stock entry
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()

        # Update Purchase Receipt Item quantities
        for item in receipt_items:
            frappe.db.set_value(
                "Purchase Receipt Item",
                {"parent": purchase_receipt, "item_code": item["item_code"]},
                {
                    "custom_qc_processing_quantity": item["qty"],
                    "custom_qc_remaining_quantity": 0
                }
            )

        return _("Stock Entry {0} has been created successfully.").format(stock_entry.name)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Auto Transfer Stock Entry Error")
        frappe.throw(_("Could not create stock entry. Error: {0}").format(str(e)))


@frappe.whitelist()
# If inspection required for particular item then make drafted stock entry from Default Inward Warehouse to Default QC Processing Warehouse
def create_draft_stock_entry_for_qc(purchase_receipt, purchase_receipt_item_id, item_code, warehouse, qty):
    try:
        qty = float(qty)

        # Fetch Default QC Processing Warehouse from QC Settings
        qc_settings = frappe.get_single("QC Settings")
        target_warehouse = qc_settings.default_qc_processing_warehouse

        if not target_warehouse:
            frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

        # Fetch batch number and serial & batch bundle from Purchase Receipt Item
        purchase_receipt_item = frappe.db.get_value(
            "Purchase Receipt Item",
            purchase_receipt_item_id,
            ["batch_no", "serial_and_batch_bundle"],
            as_dict=True
        )

        batch_no = purchase_receipt_item.get("batch_no") if purchase_receipt_item else None
        bundle_name = purchase_receipt_item.get("serial_and_batch_bundle") if purchase_receipt_item else None

        # If batch_no is not found in the item, fetch from Serial and Batch Bundle
        if not batch_no and bundle_name:
            bundle_details = frappe.get_all(
                "Serial and Batch Entry",
                filters={"parent": bundle_name},
                fields=["batch_no"]
            )

            batch_numbers = list(set(d["batch_no"] for d in bundle_details if d["batch_no"]))
            if batch_numbers:
                batch_no = batch_numbers[0]  # Assign first batch if multiple exist

        def map_item(source, target, source_parent):
            if source.item_code == item_code:
                target.s_warehouse = warehouse
                target.t_warehouse = target_warehouse
                target.qty = qty
                target.reference_purchase_receipt = purchase_receipt
                target.use_serial_batch_fields = 1 if batch_no else 0
                if batch_no:
                    target.batch_no = batch_no  # Assign batch number

        stock_entry = get_mapped_doc(
            "Purchase Receipt",
            purchase_receipt,
            {
                "Purchase Receipt": {
                    "doctype": "Stock Entry",
                    "field_map": {},
                },
                "Purchase Receipt Item": {
                    "doctype": "Stock Entry Detail",
                    "field_map": {},
                    "postprocess": map_item,
                    "condition": lambda doc: doc.item_code == item_code
                },
            },
            target_doc=None
        )

        stock_entry.stock_entry_type = "QC Transfer"
        stock_entry.purchase_receipt_no = purchase_receipt
        stock_entry.custom_from_qc = 1

        stock_entry.save(ignore_permissions=True)

        return stock_entry.name

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Stock Entry Creation Error"))
        frappe.throw(_("Could not create Stock Entry. Error: {0}").format(str(e)))
        

@frappe.whitelist()
def update_qc_quantities(purchase_receipt_item_id, new_qc_processing_qty, new_qc_remaining_qty):
    """Update QC Processing and Remaining Quantity in the Purchase Receipt Item."""

    try:
        # Convert inputs to float
        new_qc_processing_qty = float(new_qc_processing_qty)
        new_qc_remaining_qty = float(new_qc_remaining_qty)

        # Update QC Quantities using frappe.db.set_value()
        frappe.db.set_value(
            "Purchase Receipt Item",
            purchase_receipt_item_id,
            {
                "custom_qc_processing_quantity": new_qc_processing_qty,
                "custom_qc_remaining_quantity": new_qc_remaining_qty
            }
        )

        return {"status": "success", "message": "QC Processing and Remaining Quantity updated successfully."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "QC Quantity Update Error")
        frappe.throw(_("Could not update QC quantities. Error: {0}").format(str(e)))


@frappe.whitelist()
def create_stock_entry_for_material_transfer(purchase_receipt, item_code, warehouse, purchase_receipt_item_id):
    """
    Create a Stock Entry for material transfer from Default Inward Warehouse 
    to Default QC Accepted Warehouse if inspection is not required.
    """

    try:
        # Fetch Default QC Accepted Warehouse from QC Settings
        qc_settings = frappe.get_single("QC Settings")
        target_warehouse = qc_settings.default_qc_accepted_warehouse

        if not target_warehouse:
            frappe.throw(_("Default QC Accepted Warehouse is not set in QC Settings."))

        # Fetch Purchase Receipt Item details
        purchase_receipt_item = frappe.db.get_value(
            "Purchase Receipt Item",
            purchase_receipt_item_id,
            ["serial_no", "batch_no", "serial_and_batch_bundle", "qty"],
            as_dict=True,
        )

        if not purchase_receipt_item:
            frappe.throw(_("Purchase Receipt Item not found."))

        serial_no_str = purchase_receipt_item.get("serial_no")
        batch_no = purchase_receipt_item.get("batch_no")
        bundle_name = purchase_receipt_item.get("serial_and_batch_bundle")
        total_qty = purchase_receipt_item.get("qty")

        serial_numbers = []

        # Fetch batch and serial numbers if they are not directly available
        if not serial_no_str and not batch_no and bundle_name:
            bundle_details = frappe.db.get_all(
                "Serial and Batch Entry",
                filters={"parent": bundle_name},
                fields=["serial_no", "batch_no"]
            )

            batch_numbers = list(set(d["batch_no"] for d in bundle_details if d["batch_no"]))
            serial_numbers = [d["serial_no"] for d in bundle_details if d["serial_no"]]

            if batch_numbers:
                batch_no = batch_numbers[0]  # Pick the first batch if multiple exist
            if serial_numbers:
                serial_no_str = "\n".join(serial_numbers)

        # Function to map item data
        def map_item(source, target, source_parent):
            if source.item_code == item_code:
                target.s_warehouse = warehouse
                target.t_warehouse = target_warehouse
                target.qty = total_qty
                target.reference_purchase_receipt = purchase_receipt
                target.use_serial_batch_fields = 1 if serial_no_str or batch_no else 0
                if serial_no_str:
                    target.serial_no = serial_no_str
                if batch_no:
                    target.batch_no = batch_no

        # Create Stock Entry document
        stock_entry = get_mapped_doc(
            "Purchase Receipt",
            purchase_receipt,
            {
                "Purchase Receipt": {
                    "doctype": "Stock Entry",
                },
                "Purchase Receipt Item": {
                    "doctype": "Stock Entry Detail",
                    "postprocess": map_item,
                    "condition": lambda doc: doc.item_code == item_code
                },
            },
            target_doc=None
        )

        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.purchase_receipt_no = purchase_receipt
        stock_entry.custom_from_qc = 1

        stock_entry.flags.ignore_permissions = True
        stock_entry.submit()

        # Update QC Processing and Remaining Quantity using frappe.db.set_value()
        frappe.db.set_value(
            "Purchase Receipt Item",
            purchase_receipt_item_id,
            {
                "custom_qc_processing_quantity": total_qty,
                "custom_qc_remaining_quantity": 0
            }
        )

        return stock_entry.name

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Stock Entry Creation Error")
        frappe.throw(_("Could not create Stock Entry. Error: {0}").format(str(e)))


@frappe.whitelist()
def add_serial_numbers_and_approve(stock_entry, item_code, serial_numbers):
    """ Add Serial Numbers to Stock Entry and Approve """
    try:
        stock_entry_doc = frappe.get_doc("Stock Entry", stock_entry)

        # Add Serial Numbers
        for item in stock_entry_doc.items:
            if item.item_code == item_code:
                item.use_serial_batch_fields = 1
                item.serial_no = serial_numbers
                break

        stock_entry_doc.save()

        stock_entry_doc.flags.ignore_permissions = True
        stock_entry_doc.submit()

        # Send Notification
        send_notification("Stock Entry", stock_entry)

        return {"status": "success", "message": _("Serial Numbers added and Stock Entry {0} Approved Successfully.").format(stock_entry)}
        
    
    except Exception as e:
        frappe.log_error(f"Error in add_serial_numbers_and_approve: {str(e)}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}
    

@frappe.whitelist()
# Approve (submit) drafted stock entry for material transfer
def approve_stock_entry(stock_entry):

    try:
       se = frappe.get_doc("Stock Entry", stock_entry)
       se.flags.ignore_permissions = True
       se.submit()

       # Send Notification
       send_notification("Stock Entry", stock_entry)

       return {"status": "success", "message": _("Stock Entry {0} has been submitted successfully.").format(stock_entry)}
  
    except Exception as e:
       frappe.log_error(frappe.get_traceback(), _("Stock Entry Approval Error"))
       frappe.throw(_("Could not approve Stock Entry. Error: {0}").format(str(e)))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
# Filter Items based on warehouse mentioned in QC Settings --> Default QC Processing Warehouse
def get_items_from_warehouse(doctype, txt, searchfield, start, page_len, filters):

    # Fetch QC Processing warehouse from QC Settings
    qc_settings = frappe.get_single("QC Settings")
    warehouse_name = qc_settings.default_qc_processing_warehouse
    
    if not warehouse_name:
            frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

    # Fetch items from the warehouse
    return frappe.db.sql("""
            SELECT DISTINCT item_code
            FROM `tabBin`
            WHERE warehouse = %s
            AND actual_qty > 0
            AND item_code LIKE %s
            LIMIT %s, %s
        """, (warehouse_name, f"%{txt}%", start, page_len))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
# Filter Item Serial No based on selected Item Code and warehouse mentioned in QC Settings --> Default QC Processing Warehouse
def get_serial_nos(doctype, txt, searchfield, start, page_len, filters):
  
    item_code = filters.get("item_code")

    # Fetch QC Processing warehouse from QC Settings
    qc_settings = frappe.get_single("QC Settings")
    warehouse_name = qc_settings.default_qc_processing_warehouse

    if not warehouse_name:
            frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

    return frappe.db.sql("""
       SELECT name
       FROM `tabSerial No`
       WHERE item_code = %s
       AND warehouse = %s
       AND name LIKE %s
       LIMIT %s, %s
   """, (item_code, warehouse_name, f"%{txt}%", start, page_len))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
# Fetch Quality Inspection Template from Item master Quality Inspection Template field
def get_quality_inspection_templates(doctype, txt, searchfield, start, page_len, filters):

   item_code = filters.get("item_code")

   return frappe.db.sql("""
       SELECT quality_inspection_template
       FROM `tabItem`
       WHERE item_code = %s
       AND quality_inspection_template LIKE %s
       LIMIT %s, %s
   """, (item_code, f"%{txt}%", start, page_len))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_batch_nos(doctype, txt, searchfield, start, page_len, filters):
    item_code = filters.get("item_code")

    qc_settings = frappe.get_single("QC Settings")
    qc_processing_warehouse = qc_settings.default_qc_processing_warehouse

    if not qc_processing_warehouse:
        frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

    active_batches = []
    batches = get_batch_qty(item_code=item_code, warehouse=qc_processing_warehouse)

    # Filter only batches with positive qty and matching search input
    filtered_batches = [
        [batch_no] for batch_no, qty in batches.items()
        if qty > 0 and (not txt or txt.lower() in batch_no.lower())  # <-- 🔥 Filter based on user input (txt)
    ]

    return filtered_batches[start : start + page_len]  # <-- Apply pagination


# Get batch quantities using get_auto_batch_nos
@frappe.whitelist()
def get_batch_qty(
    batch_no=None,
    warehouse=None,
    item_code=None,
    posting_date=None,
    posting_time=None,
    ignore_voucher_nos=None,
    for_stock_levels=False,
):
    batchwise_qty = defaultdict(float)
    kwargs = frappe._dict(
        {
            "item_code": item_code,
            "warehouse": warehouse,
            "posting_date": posting_date,
            "posting_time": posting_time,
            "batch_no": batch_no,
            "ignore_voucher_nos": ignore_voucher_nos,
            "for_stock_levels": for_stock_levels,
        }
    )

    batches = get_auto_batch_nos(kwargs)

    for batch in batches:
        batchwise_qty[batch.get("batch_no")] += batch.get("qty")

    # If batch_no is provided, return its quantity
    if batch_no:
        return batchwise_qty.get(batch_no, 0)

    return batchwise_qty


@frappe.whitelist()
def get_item_details(item_code):
    """Fetch Quality Inspection Template, Has Serial No, and Has Batch No for an item."""
    
    item_data = frappe.db.get_value(
        "Item",
        item_code,
        ["quality_inspection_template", "has_serial_no", "has_batch_no"],
        as_dict=True
    )

    return item_data or {"error": _("Item not found")}


@frappe.whitelist()
def get_serial_batch(serial_no):
    """Fetch Batch No from Serial No."""
    
    batch_no = frappe.db.get_value("Serial No", serial_no, "batch_no")

    return {"batch_no": batch_no or ""}  # Return empty string if no batch found


@frappe.whitelist()
def get_qc_processing_warehouse():
    """Fetch Default QC Processing Warehouse from QC Settings using SQL"""
    qc_settings = frappe.get_single("QC Settings")
    qc_processing_warehouse = qc_settings.default_qc_processing_warehouse

    if not qc_processing_warehouse:
        return {"error": _("QC Processing Warehouse is not configured in QC Settings.")}

    return {"qc_processing_warehouse": qc_processing_warehouse}


@frappe.whitelist()
def get_valid_serial_numbers(purchase_receipt_id, item_code, serial_numbers):
    """
    Fetch valid serial numbers for a given Purchase Receipt ID and Item Code.
    Validate if provided serial numbers exist.
    """

    # Fetch valid serial numbers using frappe.get_all()
    valid_serial_numbers = frappe.get_all(
        "Serial No",
        filters={"purchase_document_no": purchase_receipt_id, "item_code": item_code, "status": "Active"},
        pluck="name"
    )

    # Convert serial_numbers (comma-separated) to a list and strip spaces
    entered_serials = [sn.strip() for sn in serial_numbers.split(",")] if serial_numbers else []

    # Identify invalid serial numbers
    invalid_serials = [sn for sn in entered_serials if sn not in valid_serial_numbers]

    if invalid_serials:
        return {
            "status": "error",
            "message": _("The following serial numbers are not valid for this Purchase Receipt Item: <br><b>{}</b>").format(", ".join(invalid_serials)),
            "invalid_serials": invalid_serials
        }

    return {
        "status": "success",
        "message": _("All serial numbers are valid."),
        "valid_serial_numbers": valid_serial_numbers
    }


@frappe.whitelist()
# Sample Size can not exceed total No of Items in QC Settings --> Default QC Processing Warehouse
def get_available_qty(item_code):
    """
    Fetch the available quantity of an item in the Default QC Processing Warehouse 
    defined in QC Settings. Sample size cannot exceed this quantity.
    """

    # Get Default QC Processing Warehouse from QC Settings
    qc_settings = frappe.get_single("QC Settings")
    warehouse = qc_settings.default_qc_processing_warehouse

    if not warehouse:
        return {"error": _("QC Processing Warehouse is not configured in QC Settings.")}

    # Fetch actual quantity from `tabBin`
    total_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0

    return total_qty


@frappe.whitelist()
def quality_inspection_approval(quality_inspection, actual_qty, status, workflow_save):
   
   """
   If Quality inspection status is accepted then Approve Quality inspection and create stock entry for material transfer in Accepted warehouse. And if Quality inspection status is rejected then reject Quality inspection and create stock entry for material transfer in Rejected warehouse and give stock entry reference in Quality inspection.
   """
   try:
       qi = frappe.get_doc("Quality Inspection", quality_inspection)

       if status == "Accepted":
           if workflow_save=="true":
            qi.workflow_state = "Approved"
            qi.save(ignore_permissions=True)

           stock_entry_name = create_stock_entry_for_quality_inspection(
               quality_inspection=quality_inspection,
               actual_qty=actual_qty,
               stock_entry_type="Accepted"
           )

           qi.db_set("custom_stock_entry", stock_entry_name, update_modified=False)
          
           qi.save(ignore_permissions=True)

           return {"status": "success", "message": _("Quality Inspection {0} has been approved successfully. Stock Entry: {1}").format(quality_inspection, stock_entry_name)}
      
       elif status == "Rejected":
           if workflow_save=="true":
            qi.workflow_state = "Rejected"
            qi.save(ignore_permissions=True)

           stock_entry_name = create_stock_entry_for_quality_inspection(
               quality_inspection=quality_inspection,
               actual_qty=actual_qty,
               stock_entry_type="Rejected"
           )

           qi.db_set("custom_stock_entry", stock_entry_name, update_modified=False)
          
           qi.save(ignore_permissions=True)

           return {"status": "success", "message": _("Quality Inspection {0} has been rejected successfully. Stock Entry: {1}").format(quality_inspection, stock_entry_name)}
      
       else:
           frappe.throw(_("Invalid status provided. Use 'Accepted' or 'Rejected'."))

       return {"status": "success", "message": _("Quality Inspection {0} has been approved successfully.").format(quality_inspection)}
  
   except Exception as e:
       frappe.log_error(frappe.get_traceback(), _("Quality Inspection Approval Error"))
       frappe.throw(_("Error: {0}").format(str(e)))


def create_stock_entry_for_quality_inspection(quality_inspection, actual_qty, stock_entry_type):
    """
    Creates a Stock Entry for transferring items based on QC status using SQL.
    """
    try:
        quality_inspection = frappe.get_doc("Quality Inspection", quality_inspection)

        warehouse_type = "accepted" if stock_entry_type == "Accepted" else "rejected"

        # Fetch Source and Target Warehouses from QC Settings
        qc_settings = frappe.get_single("QC Settings")
        source_warehouse = qc_settings.default_qc_processing_warehouse
        target_warehouse = getattr(qc_settings, f"default_qc_{warehouse_type}_warehouse", None)

        if not source_warehouse or not target_warehouse:
            frappe.throw(_("Source or Target Warehouse is not set in QC Settings."))

        # Validate Serial No existence in the warehouse
        if quality_inspection.item_serial_no:
            serial_no_exists = frappe.db.exists(
                "Serial No",
                {"name": quality_inspection.item_serial_no, "warehouse": source_warehouse},
            )
            if not serial_no_exists:
                frappe.throw(
                    _("Serial No {0} is not present in the warehouse {1}.").format(
                        frappe.bold(quality_inspection.item_serial_no), frappe.bold(source_warehouse)
                    )
                )

        # Create new Stock Entry using frappe.new_doc()
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.purpose = "Material Transfer"
        stock_entry.custom_from_qc = 1

        stock_entry.append(
            "items",
            {
                "item_code": quality_inspection.item_code,
                "qty": actual_qty,
                "s_warehouse": source_warehouse,
                "t_warehouse": target_warehouse,
                "use_serial_batch_fields": 1 if quality_inspection.item_serial_no or quality_inspection.batch_no else 0,
                "batch_no": quality_inspection.batch_no or None,
                "serial_no": quality_inspection.item_serial_no or None,
                "quality_inspection": quality_inspection.name,
            },
        )

        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()

        return stock_entry.name

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Stock Entry Creation Error"))
        frappe.throw(_("Could not create Stock Entry. Error: {0}").format(str(e)))


@frappe.whitelist()
def create_stock_entry(quality_inspection, rejected_stock_entry, workflow_state, target_warehouse, workflow_save):
    try:
        # Fetch Quality Inspection and update the state
        qi = frappe.get_doc("Quality Inspection", quality_inspection)
        if workflow_save=="true":
            qi.workflow_state = workflow_state
            qi.save(ignore_permissions=True)

        # Fetch source warehouse from QC Settings
        qc_settings = frappe.get_single("QC Settings")
        source_warehouse = qc_settings.default_qc_rejected_warehouse

        if not source_warehouse:
            frappe.throw(_("Source Warehouse is not set in QC Settings."))

        if not target_warehouse:
            frappe.throw(_("Target Warehouse is not set in QC Settings.."))

        # Fetch Stock Entry details from the rejected Stock Entry
        stock_entry_items = frappe.get_all(
            "Stock Entry Detail",
            filters={"parent": rejected_stock_entry},
            fields=["item_code", "qty", "serial_no", "batch_no", "quality_inspection"],
        )

        if not stock_entry_items:
            frappe.throw(_("Stock Entry {0} not found or has no items.").format(rejected_stock_entry))

        # Create a new Stock Entry using new_doc
        new_stock_entry = frappe.new_doc("Stock Entry")
        new_stock_entry.stock_entry_type = "Material Transfer"
        new_stock_entry.purpose = "Material Transfer"
        new_stock_entry.custom_stock_entry = rejected_stock_entry
        new_stock_entry.custom_from_qc = 1

        for sed in stock_entry_items:
            serial_no_str = sed.get("serial_no")
            batch_no = sed.get("batch_no")

            # Fetch Serial Numbers if the item has a serial number bundle
            if not serial_no_str:
                serial_nos = frappe.get_all(
                    "Serial No",
                    filters={"purchase_document_no": rejected_stock_entry, "item_code": sed["item_code"], "status": "Active"},
                    pluck="name"
                )
                serial_no_str = "\n".join(serial_nos) if serial_nos else None

            # Append items to the new Stock Entry
            new_stock_entry.append("items", {
                "item_code": sed["item_code"],
                "qty": sed["qty"],
                "s_warehouse": source_warehouse,
                "t_warehouse": target_warehouse,
                "use_serial_batch_fields": 1 if serial_no_str or batch_no else 0,
                "batch_no": batch_no if batch_no else None,
                "serial_no": serial_no_str if serial_no_str else None,
                "quality_inspection": sed["quality_inspection"]
            })

        new_stock_entry.insert(ignore_permissions=True)
        new_stock_entry.submit()  

        # Update Quality Inspection with new stock entry reference
        qi.db_set("custom_stock_entry", new_stock_entry.name, update_modified=False)

        return {"status": "success", "message": _("Stock Entry: {0} has been created Successfully").format(new_stock_entry.name)}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Stock Entry Creation Error"))
        frappe.throw(_("Could not create Stock Entry. Error: {0}").format(str(e)))


@frappe.whitelist()
# Create stock entry for rework
def stock_entry_for_rework(quality_inspection, rejected_stock_entry, workflow_save):

    qc_settings = frappe.get_single("QC Settings")
    target_warehouse = qc_settings.default_rework_warehouse

    if not target_warehouse:
        frappe.throw(_("Target Warehouse is not set in QC Settings."))

    return create_stock_entry(quality_inspection, rejected_stock_entry, "Rework", target_warehouse, workflow_save)


@frappe.whitelist()
# Create stock entry for return
def stock_entry_for_return(quality_inspection, rejected_stock_entry, workflow_save):

    qc_settings = frappe.get_single("QC Settings")
    target_warehouse = qc_settings.default_return_warehouse

    if not target_warehouse:
        frappe.throw(_("Target Warehouse is not set in QC Settings."))

    return create_stock_entry(quality_inspection, rejected_stock_entry, "Return", target_warehouse, workflow_save)


@frappe.whitelist()
def send_notification(doctype, doc_name):
    """
    Sends a notification when a document is submitted or reaches a specific workflow state.

    Parameters:
    - doctype (str): The document type (e.g., "Quality Inspection", "Stock Entry").
    - doc_name (str): The document name.

    Returns:
    None
    """
    try:
        doc = frappe.get_doc(doctype, doc_name)

        # Fetch Quality Managers from QC Settings
        qc_settings = frappe.get_single("QC Settings")
        quality_managers = [qm.quality_manager for qm in qc_settings.quality_manager]
        
        if not quality_managers:
            frappe.throw("No Quality Managers found in QC Settings.")

        # Define subject and message based on doctype
        if doctype == "Quality Inspection" and doc.workflow_state == "Approval Requested":
            subject = f"Quality Inspection {doc.name} - Approval Requested"
            message = f"Quality Inspection {doc.name} for {doc.item_name} is awaiting your approval."
        elif doctype == "Stock Entry":
            subject = f"QC Requested Stock Entry {doc.name} - Approved"
            message = f"Stock Entry {doc.name} has been submitted successfully."
        else:
            return

        # Send notifications to all quality managers
        for recipient in quality_managers:
            try:
                create_notification_log(
                    subject=subject,
                    content=message,
                    document_type=doctype,
                    document_name=doc.name,
                    for_user=recipient
                )
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), f"Error Sending {doctype} Notification")
                frappe.throw(f"Error while sending notification to {recipient}: {str(e)}")

        return {"status": "success", "message": "Notification Sent Successfully"}

    except Exception as e:
        frappe.log_error(f"Error in send_notification: {str(e)}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}


@frappe.whitelist()
def send_notification_on_submit(doc, method):
    """Send notification when a QC Transfer Stock Entry is submitted."""
    try:
        # Check if the Stock Entry is for QC Transfer and Stock Entry is from QC
        if doc.stock_entry_type == "QC Transfer" and doc.custom_from_qc == 1:
            send_notification("Stock Entry", doc.name)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Stock Entry QC Transfer Notification Error")
        frappe.throw(_("Failed to send notification. Error: {0}").format(str(e)))


@frappe.whitelist()
def revert_auto_transfer_stock(doc, method=None):
    """Revert auto-transferred stock when Stock Entry is canceled (Only if custom_from_qc = 1)"""
    try:
        # Check if the Stock Entry is from QC
        if doc.custom_from_qc == 1:

            # Revert custom QC quantities in Purchase Receipt Item
            for item in doc.items:
                if item.reference_purchase_receipt:
                    frappe.db.sql("""
                        UPDATE `tabPurchase Receipt Item`
                        SET 
                            custom_qc_processing_quantity = GREATEST(custom_qc_processing_quantity - %s, 0),
                            custom_qc_remaining_quantity = custom_qc_remaining_quantity + %s
                        WHERE parent = %s AND item_code = %s
                    """, (item.qty, item.qty, item.reference_purchase_receipt, item.item_code))

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Revert Auto Transfer Stock Error")
        frappe.throw(_("Could not revert stock transfer. Error: {0}").format(str(e)))


@frappe.whitelist()
def restore_qc_quantities_on_delete(doc, method):
    """Restore QC quantities in Purchase Receipt Item when a Stock Entry is deleted."""
    try:
       # Check if the Stock Entry is from QC
        if doc.custom_from_qc == 1:
        
            for item in doc.items:
                if item.reference_purchase_receipt:
                   
                    # Update QC Processing and Remaining Quantities
                    frappe.db.sql("""
                        UPDATE `tabPurchase Receipt Item`
                        SET 
                            custom_qc_processing_quantity = GREATEST(custom_qc_processing_quantity - %s, 0),
                            custom_qc_remaining_quantity = custom_qc_remaining_quantity + %s
                        WHERE parent = %s AND item_code = %s
                    """, (item.qty, item.qty, item.reference_purchase_receipt, item.item_code))

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "QC Quantity Restore Error")
        frappe.throw(_("Could not restore QC quantities. Error: {0}").format(str(e)))


@frappe.whitelist()
def update_qc_done_qty(qi_name):
    """
    update `qc_done_qty` in Stock Entry Detail when Quality Inspection is Approved or Rejected.
    """

    # Fetch Quality Inspection details
    qi = frappe.db.sql("""
        SELECT reference_name, item_code, batch_no, custom_actual_qty, workflow_state
        FROM `tabQuality Inspection`
        WHERE name = %s
    """, (qi_name,), as_dict=True)

    if not qi:
        frappe.throw(_("Quality Inspection not found."))

    qi = qi[0]  # Get the first (and only) result

    if qi["workflow_state"] not in ["Approved", "Rejected"]:
        frappe.throw(_("Quality Inspection must be Approved or Rejected to update QC Done Qty."))

    # Fetch Stock Entry Detail using SQL
    stock_entry_detail = frappe.db.sql("""
        SELECT name, custom_qc_done_qty, transfer_qty
        FROM `tabStock Entry Detail`
        WHERE parent = %s AND item_code = %s
    """, (qi["reference_name"], qi["item_code"]), as_dict=True)

    if not stock_entry_detail:
        frappe.throw(_("No matching Stock Entry Detail found for Item {0}.")
                     .format(qi["item_code"]))

    for detail in stock_entry_detail:
        new_qty = (detail["custom_qc_done_qty"] or 0) + qi["custom_actual_qty"]

        # Validate: Ensure qc_done_qty does not exceed transfer_qty
        if new_qty > detail["transfer_qty"]:
            frappe.throw(
                _("QC Done Qty ({0}) cannot be greater than Transfer Qty ({1}) for Item {2}.")
                .format(new_qty, detail["transfer_qty"], qi["item_code"])
            )

        # Update qc_done_qty using SQL
        frappe.db.sql("""
            UPDATE `tabStock Entry Detail`
            SET custom_qc_done_qty = %s
            WHERE name = %s
        """, (new_qty, detail["name"]))

    return {"message": "QC Done Qty updated successfully in Stock Entry {}".format(qi["reference_name"])}


@frappe.whitelist()
def get_stock_entry_details(reference_name):
    """Fetch qty and custom_qc_done_qty from Stock Entry to calculate custom_actual_qty"""

    stock_entry_item = frappe.db.get_value(
        "Stock Entry Detail",
        {"parent": reference_name},
        ["qty", "custom_qc_done_qty"],
        as_dict=True
    )

    if not stock_entry_item:
        frappe.throw(_("No stock entry details found for {0}").format(reference_name))

    # Calculate custom_actual_qty
    custom_actual_qty = stock_entry_item.get("qty", 0) - stock_entry_item.get("custom_qc_done_qty", 0)

    return {
        "custom_actual_qty": custom_actual_qty
    }


 