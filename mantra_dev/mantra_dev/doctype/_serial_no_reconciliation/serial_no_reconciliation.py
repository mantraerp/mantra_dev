# Copyright (c) 2024, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SerialNoReconciliation(Document):
	pass

@frappe.whitelist()
# Fetch given serial no data
def get_serial_no(doc_name):
    serial_no_reco = frappe.get_doc("Serial No Reconciliation", doc_name)
    
    serial_numbers = serial_no_reco.serial_no.splitlines()
    
    processed_serials = set()
    
    matching_serials = []
    non_matching_serials = []
    
    for serial_no in serial_numbers:
        if serial_no and serial_no not in processed_serials:
            serial_doc = frappe.get_doc("Serial No", serial_no)
            
            if serial_doc.item_code == serial_no_reco.item_code:
                matching_serials.append({
                    "serial_no": serial_no,
                    "item_code": serial_doc.item_code,
                    "warehouse": serial_doc.warehouse,
                    "status": serial_doc.status,
                })
            else:
                non_matching_serials.append(serial_no)
            
            processed_serials.add(serial_no)
    
    return {
        "matching_serials": matching_serials,
        "non_matching_serials": "\n".join(non_matching_serials)
    }


@frappe.whitelist()
# Process Serial number in bulk
# @frappe.whitelist(allow_guest=True)
def process_bulk_serial_no(doc_name):

    serial_no_reco = frappe.get_doc("Serial No Reconciliation", doc_name)
    all_records = frappe.db.get_all('Item Serial No',
        filters={
            'parent': doc_name
        },
        fields=['*'],
        as_list=False
    )

    processed_serials = set()
    for serial_no in all_records:
        if serial_no['serial_no'] not in processed_serials:
            serial_doc = frappe.get_doc("Serial No", serial_no['serial_no'])
            
            if serial_doc.item_code == serial_no_reco.item_code:
                if serial_no_reco.warehouse != serial_doc.warehouse and serial_doc.status == "Active":
                    frappe.enqueue(update_serial_no_warehouse_and_record,queue='long',job_name="Serial no warehouse {}".format(serial_no['serial_no']),timeout=10000,warehouse=serial_no_reco.warehouse,item_code=serial_doc.item_code,serial_no=serial_no['serial_no'],record_name=serial_no['name'])
                    processed_serials.add(serial_no['serial_no'])

    if len(processed_serials)!=0:
        return "Bulk update start in background. Refresh document after few minute to get updated status."

    return "No match record found!"




@frappe.whitelist()
# Update warehouse in serial no
def update_serial_no_warehouse(warehouse, item_code, serial_no):

    frappe.db.set_value("Serial No", serial_no, "warehouse", warehouse)
    frappe.db.commit() 
    
    return "success"

@frappe.whitelist()
# Update warehouse in serial no
def update_serial_no_warehouse_and_record(warehouse, item_code, serial_no,record_name):

    frappe.db.set_value("Serial No", serial_no, "warehouse", warehouse)
    frappe.db.set_value("Item Serial No", record_name, "warehouse", warehouse)
    frappe.db.commit() 

    return "success"