import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from collections import defaultdict
from erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle import get_auto_batch_nos
from mantra_dev.backend_code.globle import create_notification_log


@frappe.whitelist()
def get_auto_transfer_stock():
    """Fetch the 'auto_transfer_stock_for_non_qc_items' value from QC Settings."""
    auto_transfer_stock = frappe.db.sql("""
        SELECT value 
        FROM `tabSingles` 
        WHERE doctype = 'QC Settings' AND field = 'auto_transfer_stock_for_non_qc_items'
    """, as_dict=True)

    return {"auto_transfer_stock": int(auto_transfer_stock[0].value) if auto_transfer_stock else 0}


@frappe.whitelist()
# If auto_transfer_stock_for_non_qc_items is 1, create a stock entry for all items which do not required QC
def create_stock_entry_for_auto_transfer_stock(purchase_receipt):
   try:

       # Fetch items that do not require QC
       receipt_items = frappe.db.sql("""
            SELECT item_code, warehouse, batch_no, serial_no, serial_and_batch_bundle, qty
            FROM `tabPurchase Receipt Item`
            WHERE parent = %s AND custom_inspection_required_before_transfer_warehouse = 0
        """, (purchase_receipt,), as_dict=True)
       
       if not receipt_items:
           return
      
      # Fetch default QC accepted warehouse from tabSingles (Single DocType)
       target_warehouse = frappe.db.sql("""
            SELECT value FROM `tabSingles`
            WHERE doctype = 'QC Settings' AND field = 'default_qc_accepted_warehouse'
        """, as_dict=True)

       if not target_warehouse or not target_warehouse[0].get("value"):
            frappe.throw(_("Default QC Accepted Warehouse is not set in QC Settings."))

       target_warehouse = target_warehouse[0]["value"]

       def fetch_serial_and_batch(item):
            """Fetch serial and batch numbers from the Serial and Batch Bundle if not directly present."""
            serial_no_str = item.get("serial_no") if item else None
            batch_no = item.get("batch_no") if item else None
            bundle_name = item.get("serial_and_batch_bundle") if item else None

            if not serial_no_str and not batch_no and bundle_name:
                bundle_details = frappe.db.sql("""
                    SELECT serial_no, batch_no FROM `tabSerial and Batch Entry`
                    WHERE parent = %s
                """, (bundle_name,), as_dict=True)


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
           # Set serial numbers if available
           if serial_no_str:
                target.serial_no = serial_no_str  

           # Set batch number if available
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

       # Insert and submit stock entry
       stock_entry.insert(ignore_permissions=True)
       stock_entry.submit()

     # Update Purchase Receipt Item quantities
       for item in receipt_items:
            frappe.db.sql("""
                UPDATE `tabPurchase Receipt Item`
                SET custom_qc_processing_quantity = %s, custom_qc_remaining_quantity = 0
                WHERE parent = %s AND item_code = %s
            """, (item["qty"], purchase_receipt, item["item_code"]))

       return _("Stock Entry {0} has been created successfully.").format(stock_entry.name)


   except Exception as e:
       frappe.log_error(frappe.get_traceback(), "Auto Transfer Stock Entry Error")
       frappe.throw(_("Could not create stock entry. Error: {0}").format(str(e)))


@frappe.whitelist()
def get_valid_serial_numbers(purchase_receipt_id, item_code, serial_numbers):
    """
    Fetch valid serial numbers for a given Purchase Receipt ID and Item Code.
    Validate if provided serial numbers exist.
    """
    if not purchase_receipt_id or not item_code:
        return {"status": "error", "message": _("Missing required parameters.")}

    # Fetch valid serial numbers from Serial No doctype
    valid_serial_numbers = frappe.db.sql("""
        SELECT name FROM `tabSerial No`
        WHERE purchase_document_no = %s AND item_code = %s AND status = 'Active'
    """, (purchase_receipt_id, item_code), as_dict=True)

    valid_serial_numbers = [sn["name"] for sn in valid_serial_numbers]

    # Convert serial_numbers (comma-separated) to a list
    entered_serials = serial_numbers.split(",") if serial_numbers else []

    # Check for invalid serial numbers
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
# If inspection required for particular item then make drafted stock entry from Default Inward Warehouse to Default QC Processing Warehouse
def create_draft_stock_entry_for_qc(purchase_receipt, purchase_receipt_item_id, item_code, warehouse, qty):
  
   try:
    
       qty = float(qty)

       # Fetch Default QC Processing Warehouse from QC Settings
       target_warehouse = frappe.db.sql("""
            SELECT value FROM `tabSingles`
            WHERE doctype = 'QC Settings' AND field = 'default_qc_processing_warehouse'
        """, as_dict=True)

       if not target_warehouse or not target_warehouse[0].get("value"):
            frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

       target_warehouse = target_warehouse[0]["value"]

       # Fetch batch number and serial & batch bundle from Purchase Receipt Item
       purchase_receipt_item = frappe.db.sql("""
            SELECT batch_no, serial_and_batch_bundle FROM `tabPurchase Receipt Item`
            WHERE name = %s
        """, (purchase_receipt_item_id,), as_dict=True)

       batch_no = purchase_receipt_item[0]["batch_no"] if purchase_receipt_item else None
       bundle_name = purchase_receipt_item[0]["serial_and_batch_bundle"] if purchase_receipt_item else None

       if not batch_no and bundle_name:

             # Fetch batch number from Serial and Batch Bundle
            bundle_details = frappe.db.sql("""
                SELECT batch_no FROM `tabSerial and Batch Entry`
                WHERE parent = %s
            """, (bundle_name,), as_dict=True)

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


       stock_entry.save(ignore_permissions=True)

       return stock_entry.name
  
   except Exception as e:
       frappe.log_error(frappe.get_traceback(), _("Stock Entry Creation Error"))
       frappe.throw(_("Could not create Stock Entry. Error: {0}").format(str(e)))


@frappe.whitelist()
def update_qc_quantities(purchase_receipt_item_id, new_qc_processing_qty, new_qc_remaining_qty):
    """Update QC Processing and Remaining Quantity directly in the database."""

    try:
        # Convert to float
        new_qc_processing_qty = float(new_qc_processing_qty)
        new_qc_remaining_qty = float(new_qc_remaining_qty)

        # Update QC  Quantities in Purchase Receipt Item
        frappe.db.sql("""
            UPDATE `tabPurchase Receipt Item`
            SET custom_qc_processing_quantity = %s, 
                custom_qc_remaining_quantity = %s
            WHERE name = %s
        """, (new_qc_processing_qty, new_qc_remaining_qty, purchase_receipt_item_id))

        return {"status": "success", "message": "QC Processing and Remaining Quantity updated successfully."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("QC Quantity Update Error"))
        frappe.throw(_("Could not update QC quantities. Error: {0}").format(str(e)))


@frappe.whitelist()
# If inspection not required for particular item then make drafted stock entry from Default Inward Warehouse to Default QC Accepted Warehouse
def create_draft_stock_entry_for_material_transfer(purchase_receipt, item_code, warehouse, purchase_receipt_item_id):


   try:
       
       # Fetch target warehouse using raw SQL from tabSingle
       target_warehouse = frappe.db.sql("""
            SELECT value FROM `tabSingles`
            WHERE doctype = 'QC Settings' AND field = 'default_qc_accepted_warehouse'
        """, as_dict=True)

       if not target_warehouse or not target_warehouse[0].get("value"):
            frappe.throw(_("Default QC Accepted Warehouse is not set in QC Settings."))

       target_warehouse = target_warehouse[0]["value"]

       # Fetch necessary fields from Purchase Receipt Item using SQL
       purchase_receipt_item = frappe.db.sql("""
            SELECT serial_no, batch_no, serial_and_batch_bundle, qty
            FROM `tabPurchase Receipt Item`
            WHERE name = %s
        """, (purchase_receipt_item_id,), as_dict=True)
       
       serial_no_str = purchase_receipt_item[0].get("serial_no") if purchase_receipt_item else None
       batch_no = purchase_receipt_item[0].get("batch_no") if purchase_receipt_item else None
       bundle_name = purchase_receipt_item[0].get("serial_and_batch_bundle") if purchase_receipt_item else None
       total_qty = purchase_receipt_item[0].get("qty") if purchase_receipt_item else None

       serial_numbers = []

       if not serial_no_str and not batch_no and bundle_name:
            # Fetch batch and serial numbers from Serial and Batch Entry using SQL
            bundle_details = frappe.db.sql("""
                SELECT serial_no, batch_no 
                FROM `tabSerial and Batch Entry` 
                WHERE parent = %s
            """, (bundle_name,), as_dict=True)

            batch_numbers = list(set(d["batch_no"] for d in bundle_details if d["batch_no"]))
            serial_numbers = [d["serial_no"] for d in bundle_details if d["serial_no"]]

            if batch_numbers:
                batch_no = batch_numbers[0]  # Pick the first batch if multiple exist
            if serial_numbers:
                serial_no_str = "\n".join(serial_numbers)
             
       def map_item(source, target, source_parent):
            if source.item_code == item_code:
                target.s_warehouse = warehouse
                target.t_warehouse = target_warehouse
                target.qty = total_qty
                target.reference_purchase_receipt = purchase_receipt
                target.use_serial_batch_fields = 1 if serial_no_str or batch_no else 0
                if serial_no_str:
                    target.serial_no = serial_no_str  # Attach Serial Numbers
                if batch_no:
                    target.batch_no = batch_no  # Attach Batch No


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

       stock_entry.stock_entry_type = "Material Transfer"
       stock_entry.purchase_receipt_no = purchase_receipt

       stock_entry.flags.ignore_permissions = True
       stock_entry.submit()

     # Use SQL to update QC Processing and Remaining Quantity
       frappe.db.sql("""
            UPDATE `tabPurchase Receipt Item`
            SET custom_qc_processing_quantity = %s, 
                custom_qc_remaining_quantity = 0
            WHERE name = %s
        """, (total_qty, purchase_receipt_item_id))

       return stock_entry.name
  
   except Exception as e:
       frappe.log_error(frappe.get_traceback(), _("Stock Entry Creation Error"))
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
    warehouse = frappe.db.sql("""
            SELECT value 
            FROM `tabSingles` 
            WHERE doctype = 'QC Settings' AND field = 'default_qc_processing_warehouse'
        """, as_dict=True)
    
    if not warehouse or not warehouse[0].get("value"):
            frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

    warehouse_name = warehouse[0]["value"]

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
    if not item_code:
       frappe.throw(_("Item Code is required to filter Serial Nos."))

    # Fetch QC Processing warehouse from QC Settings
    warehouse = frappe.db.sql("""
            SELECT value 
            FROM `tabSingles` 
            WHERE doctype = 'QC Settings' AND field = 'default_qc_processing_warehouse'
        """, as_dict=True)
    
    if not warehouse or not warehouse[0].get("value"):
            frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

    warehouse_name = warehouse[0]["value"]


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
   if not item_code:
       frappe.throw(_("Item Code is required to fetch Quality Inspection Templates."))

   return frappe.db.sql("""
       SELECT quality_inspection_template
       FROM `tabItem`
       WHERE item_code = %s
       AND quality_inspection_template LIKE %s
       LIMIT %s, %s
   """, (item_code, f"%{txt}%", start, page_len))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
# Filter Batch No based on selected Item Code and warehouse mentioned in QC Settings --> Default QC Processing Warehouse
def get_batch_nos(doctype, txt, searchfield, start, page_len, filters):

    item_code = filters.get("item_code")
    if not item_code:
        frappe.throw(_("Item Code is required to filter Batch Nos."))

    # warehouse = frappe.db.get_single_value("QC Settings", "default_qc_processing_warehouse")
    # if not warehouse:
    #     frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

    # Fetch QC Processing warehouse from QC Settings
    warehouse = frappe.db.sql("""
            SELECT value 
            FROM `tabSingles` 
            WHERE doctype = 'QC Settings' AND field = 'default_qc_processing_warehouse'
        """, as_dict=True)
    
    if not warehouse or not warehouse[0].get("value"):
            frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))

    warehouse_name = warehouse[0]["value"]

    active_batches = []

    batches = get_batch_qty(
        item_code=item_code,
        warehouse=warehouse_name
    )

    for batch_no, qty in batches.items():
        if qty > 0:
            active_batches.append(batch_no)

    return [[batch_no] for batch_no in active_batches]


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
    """Fetch Quality Inspection Template, Has Serial No, and Has Batch No using SQL"""
    
    item_data = frappe.db.sql("""
        SELECT quality_inspection_template, has_serial_no, has_batch_no 
        FROM `tabItem` 
        WHERE item_code = %s
    """, (item_code,), as_dict=True)

    if not item_data:
        return {"error": _("Item not found")}

    return item_data[0]  # Return the first result


@frappe.whitelist()
def get_serial_batch(serial_no):
    """Fetch Batch No from Serial No using SQL"""

    batch_data = frappe.db.sql("""
        SELECT batch_no 
        FROM `tabSerial No` 
        WHERE name = %s
    """, (serial_no,), as_dict=True)

    if not batch_data or not batch_data[0].get("batch_no"):
        return {"batch_no": ""}  # Return empty if no batch found

    return {"batch_no": batch_data[0]["batch_no"]}


@frappe.whitelist()
def get_qc_processing_warehouse():
    """Fetch Default QC Processing Warehouse from QC Settings using SQL"""
    warehouse_data = frappe.db.sql("""
        SELECT value 
        FROM `tabSingles` 
        WHERE doctype = 'QC Settings' AND field = 'default_qc_processing_warehouse'
    """, as_dict=True)

    if not warehouse_data or not warehouse_data[0].get("value"):
        return {"error": _("QC Processing Warehouse is not configured in QC Settings.")}

    return {"qc_processing_warehouse": warehouse_data[0]["value"]}


@frappe.whitelist()
# Sample Size can not exceed total No of Items in QC Settings --> Default QC Processing Warehouse
def get_available_qty(item_code):
  
    if not item_code:
       frappe.throw(_("Item Code is required to validate Sample Size."))

    warehouse_data = frappe.db.sql("""
        SELECT value 
        FROM `tabSingles` 
        WHERE doctype = 'QC Settings' AND field = 'default_qc_processing_warehouse'
    """, as_dict=True)

    if not warehouse_data or not warehouse_data[0].get("value"):
        return {"error": _("QC Processing Warehouse is not configured in QC Settings.")}
    
    warehouse = warehouse_data[0]["value"]

    total_qty = frappe.db.sql("""
        SELECT actual_qty 
        FROM `tabBin`
        WHERE item_code = %s AND warehouse = %s
    """, (item_code, warehouse))

    return total_qty[0][0] if total_qty else 0


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

        warehouses = frappe.db.sql(
            """
            SELECT 
                (SELECT value FROM `tabSingles` WHERE doctype = 'QC Settings' AND field = 'default_qc_processing_warehouse') AS source_warehouse,
                (SELECT value FROM `tabSingles` WHERE doctype = 'QC Settings' AND field = 'default_qc_{0}_warehouse') AS target_warehouse
            """.format(warehouse_type),
            as_dict=True,
        )[0]

        source_warehouse, target_warehouse = warehouses["source_warehouse"], warehouses["target_warehouse"]

        if not source_warehouse or not target_warehouse:
            frappe.throw(_("Source or Target Warehouse is not set in QC Settings."))

        # Validate Serial No existence
        if quality_inspection.item_serial_no:
            serial_no_exists = frappe.db.sql(
                """
                SELECT name FROM `tabSerial No`
                WHERE name = %s AND warehouse = %s
                """,
                (quality_inspection.item_serial_no, source_warehouse),
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
        source_warehouse = frappe.db.sql(
            """SELECT value FROM `tabSingles` WHERE doctype = 'QC Settings' AND field = 'default_qc_rejected_warehouse'""",
            as_dict=True,
        )
        if not source_warehouse or not source_warehouse[0].get("value"):
            frappe.throw(_("Source Warehouse is not set in QC Settings."))

        source_warehouse = source_warehouse[0]["value"]

        if not target_warehouse:
            frappe.throw(_("Target Warehouse is not set in QC Settings.."))

        # Fetch Stock Entry details
        stock_entry_items = frappe.db.sql(
            """SELECT item_code, qty, serial_no, batch_no, quality_inspection 
               FROM `tabStock Entry Detail` 
               WHERE parent = %s""",
            (rejected_stock_entry,),
            as_dict=True,
        )
        if not stock_entry_items:
            frappe.throw(_("Stock Entry {0} not found.").format(rejected_stock_entry))

        # Create a new Stock Entry using new_doc
        new_stock_entry = frappe.new_doc("Stock Entry")
        new_stock_entry.stock_entry_type = "Material Transfer"
        new_stock_entry.purpose = "Material Transfer"
        new_stock_entry.custom_stock_entry = rejected_stock_entry

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

    target_warehouse = frappe.db.sql(
        """SELECT value FROM `tabSingles` WHERE doctype = 'QC Settings' AND field = 'default_rework_warehouse'""",
        as_dict=True,
    )
    if not target_warehouse or not target_warehouse[0].get("value"):
        frappe.throw(_("Target Warehouse is not set in QC Settings."))

    return create_stock_entry(quality_inspection, rejected_stock_entry, "Rework", target_warehouse[0]["value"], workflow_save)

@frappe.whitelist()
# Create stock entry for return
def stock_entry_for_return(quality_inspection, rejected_stock_entry, workflow_save):

    target_warehouse = frappe.db.sql(
        """SELECT value FROM `tabSingles` WHERE doctype = 'QC Settings' AND field = 'default_return_warehouse'""",
        as_dict=True,
    )
    if not target_warehouse or not target_warehouse[0].get("value"):
        frappe.throw(_("Target Warehouse is not set in QC Settings."))

    return create_stock_entry(quality_inspection, rejected_stock_entry, "Return", target_warehouse[0]["value"], workflow_save)


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
        quality_managers = frappe.db.sql("""
            SELECT quality_manager 
            FROM `tabQuality Manager` 
            WHERE parent = 'QC Settings'
        """, as_list=True)

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
                    for_user=recipient[0]
                )
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), f"Error Sending {doctype} Notification")
                frappe.throw(f"Error while sending notification to {recipient[0]}: {str(e)}")

        return {"status": "success", "message": "Notification Sent Successfully"}

    except Exception as e:
        frappe.log_error(f"Error in send_notification: {str(e)}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}

@frappe.whitelist()
def revert_auto_transfer_stock(doc, method=None):
    """Revert auto-transferred stock when Stock Entry is canceled"""
    try:

        source_warehouse = frappe.db.sql(
        """SELECT value FROM `tabSingles` WHERE doctype = 'QC Settings' AND field = 'default_inward_warehouse'""",
        as_dict=True,
        )

        if not source_warehouse or not source_warehouse[0].get("value"):
            frappe.throw(_("Target Warehouse is not set in QC Settings."))

        source_warehouse = source_warehouse[0]["value"]

        # frappe.throw(source_warehouse)
        # return

        # Get items from the canceled Stock Entry
        stock_entry_items = frappe.db.sql("""
            SELECT item_code, qty, reference_purchase_receipt 
            FROM `tabStock Entry Detail`
            WHERE parent = %s AND reference_purchase_receipt IS NOT NULL AND s_warehouse = %s
        """, (doc.name, source_warehouse), as_dict=True)

        if not stock_entry_items:
            return

        # Revert custom_qc_processing_quantity and update custom_qc_remaining_quantity
        for item in stock_entry_items:
            frappe.db.sql("""
                UPDATE `tabPurchase Receipt Item`
                SET 
                    custom_qc_processing_quantity = custom_qc_processing_quantity - %s,
                    custom_qc_remaining_quantity = custom_qc_remaining_quantity + %s
                WHERE parent = %s AND item_code = %s
            """, (item["qty"], item["qty"], item["reference_purchase_receipt"], item["item_code"]))

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Revert Auto Transfer Stock Error")
        frappe.throw(_("Could not revert stock transfer. Error: {0}").format(str(e)))



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
