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
# Update warehouse in serial no
def update_serial_no_warehouse(warehouse, item_code, serial_no):

    frappe.db.set_value("Serial No", serial_no, "warehouse", warehouse)
    frappe.db.commit() 
    
    return "success"