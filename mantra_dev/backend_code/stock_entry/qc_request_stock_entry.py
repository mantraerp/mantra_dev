import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
# If inspection required for particular item then make drafted stock entry from Default Inward Warehouse to Default QC Processing Warehouse
def create_draft_stock_entry_for_qc(purchase_receipt, item_code, warehouse):
  
   try:


       target_warehouse = frappe.db.get_single_value("QC Settings", "default_qc_processing_warehouse")


       if not target_warehouse:
           frappe.throw(_("Default QC Processing Warehouse is not set in QC Settings."))


       def map_item(source, target, source_parent):
           target.s_warehouse = warehouse
           target.t_warehouse = target_warehouse


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


       frappe.db.set_value(
           "Purchase Receipt Item",
           {"parent": purchase_receipt, "item_code": item_code},
           "custom_stock_entry",
           stock_entry.name
       )


       return stock_entry.name
  
   except Exception as e:
       frappe.log_error(frappe.get_traceback(), _("Stock Entry Creation Error"))
       frappe.throw(_("Could not create Stock Entry. Error: {0}").format(str(e)))




@frappe.whitelist()
# If inspection not required for particular item then make drafted stock entry from Default Inward Warehouse to Default QC Accepted Warehouse
def create_draft_stock_entry_for_material_transfer(purchase_receipt, item_code, warehouse):


   try:
       target_warehouse = frappe.db.get_single_value("QC Settings", "default_qc_accepted_warehouse")


       if not target_warehouse:
           frappe.throw(_("Default QC Accepted Warehouse is not set in QC Settings."))


       def map_item(source, target, source_parent):
           target.s_warehouse = warehouse
           target.t_warehouse = target_warehouse


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


       stock_entry.save(ignore_permissions=True)


       frappe.db.set_value(
           "Purchase Receipt Item",
           {"parent": purchase_receipt, "item_code": item_code},
           "custom_stock_entry",
           stock_entry.name
       )


       return stock_entry.name
  
   except Exception as e:
       frappe.log_error(frappe.get_traceback(), _("Stock Entry Creation Error"))
       frappe.throw(_("Could not create Stock Entry. Error: {0}").format(str(e)))




@frappe.whitelist()
# Approve drafted stock entry for material transfer
def approve_stock_entry(stock_entry):


   try:
       se = frappe.get_doc("Stock Entry", stock_entry)
       se.submit()


       return {"status": "success", "message": _("Stock Entry {0} has been submitted successfully.").format(stock_entry)}
  
   except Exception as e:
       frappe.log_error(frappe.get_traceback(), _("Stock Entry Approval Error"))
       frappe.throw(_("Could not approve Stock Entry. Error: {0}").format(str(e)))
      


@frappe.whitelist()
def quality_inspection_approval(quality_inspection, status):
   """
   If Quality inspection status is accepted then Approve Quality inspection and create stock entry for material transfer in Accepted warehouse. And if Quality inspection status is rejected then reject Quality inspection and create stock entry for material transfer in Rejected warehouse and give stock entry reference in Quality inspection.
   """
   try:
       qi = frappe.get_doc("Quality Inspection", quality_inspection)


       if status == "Accepted":
           qi.workflow_state = "Approved"
           qi.save(ignore_permissions=True)


           stock_entry_name = create_stock_entry_for_quality_inspection(
               quality_inspection=qi,
               stock_entry_type="Accepted"
           )


           return {"status": "success", "message": _("Quality Inspection {0} has been approved successfully. Stock Entry: {1}").format(quality_inspection, stock_entry_name)}
      
       elif status == "Rejected":
           qi.workflow_state = "Rejected"
           qi.save(ignore_permissions=True)


           stock_entry_name = create_stock_entry_for_quality_inspection(
               quality_inspection=qi,
               stock_entry_type="Rejected"
           )


           qi.db_set("custom_rejected_stock_entry", stock_entry_name, update_modified=False)
          
           qi.save(ignore_permissions=True)


           return {"status": "success", "message": _("Quality Inspection {0} has been rejected successfully. Stock Entry: {1}").format(quality_inspection, stock_entry_name)}
      
       else:
           frappe.throw(_("Invalid status provided. Use 'Accepted' or 'Rejected'."))


       return {"status": "success", "message": _("Quality Inspection {0} has been approved successfully.").format(quality_inspection)}
  
   except Exception as e:
       frappe.log_error(frappe.get_traceback(), _("Quality Inspection Approval Error"))
       frappe.throw(_("Could not approve Quality Inspection. Error: {0}").format(str(e)))


def create_stock_entry_for_quality_inspection(quality_inspection, stock_entry_type):
    try:

        if stock_entry_type == "Accepted":
            source_warehouse = frappe.db.get_single_value("QC Settings", "default_qc_processing_warehouse")
            target_warehouse = frappe.db.get_single_value("QC Settings", "default_qc_accepted_warehouse")
        elif stock_entry_type == "Rejected":
            source_warehouse = frappe.db.get_single_value("QC Settings", "default_qc_processing_warehouse")
            target_warehouse = frappe.db.get_single_value("QC Settings", "default_qc_rejected_warehouse")
        else:
            frappe.throw(_("Invalid stock entry type: {0}").format(stock_entry_type))

        if not source_warehouse or not target_warehouse:
            frappe.throw(_("Source or Target Warehouse is not set in QC Settings."))

        qty = quality_inspection.sample_size or 1
        use_serial_batch_fields = 0
        serial_no = None
        batch_no = None

        if quality_inspection.item_serial_no and quality_inspection.batch_no:
            serial_no = quality_inspection.item_serial_no
            batch_no = quality_inspection.batch_no
            use_serial_batch_fields = 1
            qty = 1 

        elif quality_inspection.item_serial_no:
            serial_no = quality_inspection.item_serial_no
            use_serial_batch_fields = 1
            qty = 1 

        elif quality_inspection.batch_no:
            batch_no = quality_inspection.batch_no
            use_serial_batch_fields = 1
            batch_size = frappe.db.get_value("Batch", quality_inspection.batch_no, "batch_qty")
            if not batch_size:
                frappe.throw(_("Batch {0} does not have a defined size.").format(quality_inspection.batch_no))
            qty = batch_size

        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "purpose": "Material Transfer",
            "items": [
                {
                    "item_code": quality_inspection.item_code,
                    "qty": qty,  
                    "s_warehouse": source_warehouse,
                    "t_warehouse": target_warehouse,
                    "use_serial_batch_fields": use_serial_batch_fields,
                    "batch_no": batch_no if batch_no else None,
                    "serial_no": serial_no if serial_no else None,
                }
            ]
        })
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()

        return stock_entry.name

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Stock Entry Creation Error"))
        frappe.throw(_("Could not create Stock Entry. Error: {0}").format(str(e)))


@frappe.whitelist()
# If auto_transfer_stock is 1, create a stock entry for all items which do not required QC
def create_stock_entry_for_auto_transfer_stock(purchase_receipt):
   try:


       receipt_items = frappe.get_all(
           "Purchase Receipt Item",
           filters={"parent": purchase_receipt, "custom_inspection_required_before_transfer_warehouse": 0},
           fields=["item_code", "warehouse"]
       )
       if not receipt_items:
           return
      
       target_warehouse = frappe.db.get_single_value("QC Settings", "default_qc_accepted_warehouse")
       if not target_warehouse:
           frappe.throw(_("Default QC Accepted Warehouse is not set in QC Settings."))


       def map_item(source, target, source_parent):
           target.s_warehouse = source.warehouse
           target.t_warehouse = target_warehouse


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


       # stock_entry.save(ignore_permissions=True)
       stock_entry.insert(ignore_permissions=True)
       stock_entry.submit()


       for item in receipt_items:
           frappe.db.set_value(
               "Purchase Receipt Item",
               {"parent": purchase_receipt, "item_code": item["item_code"]},
               "custom_stock_entry",
               stock_entry.name
           )


       return _("Stock Entry {0} has been created successfully.").format(stock_entry.name)


   except Exception as e:
       frappe.log_error(frappe.get_traceback(), "Auto Transfer Stock Entry Error")
       frappe.throw(_("Could not create stock entry. Error: {0}").format(str(e)))
