import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
import json

# @frappe.whitelist()
# def make_dc(doc, method=None):
#     custom_settings = frappe.get_single('Custom Settings')

#     if custom_settings.auto_create_delivery_note == 1:
#         print("Sales Invoice Name:", doc.name)
#         frappe.msgprint(str(len(doc.items)))
#         if len(doc.items) == 1:
#             for item in doc.items:
#                 if not item.get('item_code'):
#                     is_service_item = frappe.db.get_value("Item", item.get('item_code'), 'custom_is_service_item')
#                     if is_service_item == 0:
#                         dc = frappe.new_doc("Delivery Note")
#                         dc.custom_sales_invoice_no = doc.name
#                         dc.customer = doc.customer
#                         dc.posting_date = doc.posting_date
#                         dc.posting_time = doc.posting_time
#                         dc.custom_sales_person = doc.custom_sales_person
#                         dc.company = doc.company
#                         dc.set_warehouse = doc.set_warehouse
#                         dc.dispatch_address_name = ""
#                         dc.items = []
#                         print("Processing Item:", item)
#                         if not item.get('item_code'):
#                             frappe.throw("Item code is missing in one of the items.")
#                         else:
#                                 dn_item = dc.append('items', {})
#                                 dn_item.item_code = item.item_code
#                                 dn_item.item_name = item.item_name
#                                 dn_item.qty = item.qty
#                                 dn_item.uom = item.uom
#                                 dn_item.rate = item.rate
#                                 dn_item.amount = item.amount
#                                 dn_item.against_sales_invoice = doc.name
#                                 dn_item.si_detail = item.name
#                                 if item.get('sales_order'):
#                                     dn_item.against_sales_order = item.sales_order
#                                     dn_item.so_detail = item.so_detail
#                         dc.total = doc.total if doc.total is not None else 0
#                         dc.net_total = doc.net_total if doc.net_total is not None else 0
#                         dc.grand_total = doc.grand_total if doc.grand_total is not None else 0
#                         dc.base_total = doc.base_total if doc.base_total is not None else 0
#                         dc.base_net_total = doc.base_net_total if doc.base_net_total is not None else 0
#                         dc.base_grand_total = doc.base_grand_total if doc.base_grand_total is not None else 0
#                         dc.insert(ignore_permissions=True)
#                         frappe.db.commit()
#                         for dc_items in dc.items:
#                             if dc_items.so_detail:
#                                 qty = frappe.db.get_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty")
#                                 print(qty)
#                                 if qty is None:
#                                     qty = 0
#                                 t_qty = qty + dc_items.qty
#                                 frappe.db.set_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty", t_qty)
#                         frappe.db.commit()
#                         frappe.msgprint(f"Delivery Note {dc.name} created successfully.")
#         else:
#             dc = frappe.new_doc("Delivery Note")
#             dc.custom_sales_invoice_no = doc.name
#             dc.customer = doc.customer
#             dc.posting_date = doc.posting_date
#             dc.posting_time = doc.posting_time
#             dc.custom_sales_person = doc.custom_sales_person
#             dc.company = doc.company
#             dc.set_warehouse = doc.set_warehouse
#             dc.dispatch_address_name = ""
#             dc.items = []
#             for item in doc.items:
#                 print("Processing Item:", item)
#                 if not item.get('item_code'):
#                     frappe.throw("Item code is missing in one of the items.")
#                 else:
#                     is_service_item = frappe.db.get_value("Item", item.get('item_code'), 'custom_is_service_item')
#                     if is_service_item == 0:
#                         dn_item = dc.append('items', {})
#                         dn_item.item_code = item.item_code
#                         dn_item.item_name = item.item_name
#                         dn_item.qty = item.qty
#                         dn_item.uom = item.uom
#                         dn_item.rate = item.rate
#                         dn_item.amount = item.amount
#                         dn_item.against_sales_invoice = doc.name
#                         dn_item.si_detail = item.name
#                         if item.get('sales_order'):
#                             dn_item.against_sales_order = item.sales_order
#                             dn_item.so_detail = item.so_detail
#             dc.total = doc.total if doc.total is not None else 0
#             dc.net_total = doc.net_total if doc.net_total is not None else 0
#             dc.grand_total = doc.grand_total if doc.grand_total is not None else 0
#             dc.base_total = doc.base_total if doc.base_total is not None else 0
#             dc.base_net_total = doc.base_net_total if doc.base_net_total is not None else 0
#             dc.base_grand_total = doc.base_grand_total if doc.base_grand_total is not None else 0

        
#             dc.insert(ignore_permissions=True)
#             frappe.db.commit()
#             for dc_items in dc.items:
#                 if dc_items.so_detail:
#                     qty = frappe.db.get_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty")
#                     print(qty)
#                     if qty is None:
#                         qty = 0
#                     t_qty = qty + dc_items.qty
#                     frappe.db.set_value("Sales Order Item", dc_items.so_detail, "custom_draft_deliverd_qty", t_qty)
#             frappe.db.commit()
#             frappe.msgprint(f"Delivery Note {dc.name} created successfully.")
       


@frappe.whitelist()
def create_delivery_note(**args):
    
    if frappe.get_single('Custom Settings').auto_create_delivery_note==0:
         return True

    
    try:
        doc = json.loads(args['data'])
        if doc['einvoice_status'] == "Not Applicable":
            delivery_note = get_mapped_doc(
            "Sales Invoice", 
            doc['name'], {
                "Sales Invoice": {
                    "doctype": "Delivery Note",
                    "field_map": {
                        "name": 'against_sales_invoice',
                        "customer": "customer",
                        "posting_date": "posting_date"
                    }
                },
                "Sales Invoice Item": {
                    "doctype": "Delivery Note Item",
                    "field_map": {
                        "name": "si_detail",  # Link to Sales Invoice Item row
                        "item_code": "item_code",
                        "qty": "qty",
                        "rate": "rate",
                        "parent": "against_sales_invoice",
                    }
                }
            },
            target_doc=None
            )
            delivery_note.save()
            frappe.msgprint(f"Delivery Note created.")
            # frappe.msgprint(f"Delivery Note {delivery_note.name} created for Sales Invoice {doc['name']}")
            
        elif doc['einvoice_status'] == "Generated":
            delivery_note = get_mapped_doc(
            "Sales Invoice", 
            doc['name'], {
                "Sales Invoice": {
                    "doctype": "Delivery Note",
                    "field_map": {
                        "name": 'against_sales_invoice',
                        "customer": "customer",
                        "posting_date": "posting_date"
                    }
                },
                "Sales Invoice Item": {
                    "doctype": "Delivery Note Item",
                    "field_map": {
                        "name": "si_detail",  # Link to Sales Invoice Item row
                        "item_code": "item_code",
                        "qty": "qty",
                        "rate": "rate",
                        "parent": "against_sales_invoice",
                    }
                }
            }, 
            target_doc=None
            )
            delivery_note.save()
            frappe.msgprint(f"Delivery Note created.")
            # frappe.msgprint(f"Delivery Note {delivery_note.name} created for Sales Invoice {doc['name']}")
        
        
        # else:
        #     # frappe.msgprint("NO")
        #     raise Exception(", Sorry")
    except Exception as e:
        frappe.msgprint("Delivery Note is not created {}".format(str(e)))