import frappe
from datetime import datetime
from frappe.utils import flt

@frappe.whitelist()
def update_purchase_order_expected_date(doc, method=None):
    pass
    # if doc.workflow_state == 'Approved':
    #     for item in doc.items:
    #         if item.purchase_order:
    #             total_qty = item.qty
    #             received_qty = 0
    #             # Fetch all relevant records in a single query
    #             purchase_order_expected_list = frappe.db.get_list(
    #                 "Purchase Order Expected Date", 
    #                 filters={'item_code': item.item_code,'purchase_order':item.purchase_order},
    #                 fields=['name', 'expected_qty', 'qty', 'received_qty', 'final_expected_receive_date', 'purchase_order', 'creation','total_qty'],
    #                 order_by='`tabPurchase Order Expected Date`.creation asc'
    #             )
    #             if item.schedule_date:
    #             # Scenario 1: Filter records where final_expected_receive_date == item.schedule_date and qty == item.qty
    #                 purchase_order_expected_list_1 = [data for data in purchase_order_expected_list if data.final_expected_receive_date == item.schedule_date and data.expected_qty == item.qty]
    #                 # Scenario 2: Filter records where final_expected_receive_date < item.schedule_date
    #                 purchase_order_expected_list_2 = [data for data in purchase_order_expected_list if data.final_expected_receive_date >= item.schedule_date]
    #                 # Scenario 3: Filter records where final_expected_receive_date > item.schedule_date
    #                 purchase_order_expected_list_3 = [data for data in purchase_order_expected_list if data.final_expected_receive_date <= item.schedule_date]
    #                 # Scenario 4: Filter records where none of the above conditions are met
    
    #                 # Now we will combine the filtered lists according to the priority order:
    #                 all_purchase_order_expected = []
    #                 if purchase_order_expected_list_1:
    #                     all_purchase_order_expected = purchase_order_expected_list_1
    #                 elif purchase_order_expected_list_2:
    #                     all_purchase_order_expected = purchase_order_expected_list_2
    #                 elif purchase_order_expected_list_3:
    #                     all_purchase_order_expected = purchase_order_expected_list_3
    #                 all_purchase_order_expected = (
    #                         purchase_order_expected_list_1 if not len(purchase_order_expected_list_1) > 1 else sorted(purchase_order_expected_list_1, key=lambda x: x['creation'])
    #                     ) + (
    #                         purchase_order_expected_list_2 if not len(purchase_order_expected_list_2) > 1 else sorted(purchase_order_expected_list_2, key=lambda x: x['creation'])
    #                     ) + (
    #                         purchase_order_expected_list_3 if not len(purchase_order_expected_list_3) > 1 else sorted(purchase_order_expected_list_3, key=lambda x: x['creation'])
    #                     )
    #                 unique_purchase_orders = {item['name']: item for item in all_purchase_order_expected}.values()

    #                 # Convert back to a list
    #                 all_purchase_order_expected = list(unique_purchase_orders)
    #                 # Convert back to a list and sort by 'creation'
    #                 for data in all_purchase_order_expected:
    #                     expected_qty = data.total_qty
    #                     if received_qty + expected_qty <= total_qty:
    #                         # Update received and expected quantities
    #                         frappe.db.set_value("Purchase Order Expected Date", data.name, 'total_qty',abs(data.total_qty - abs((expected_qty))))
    #                         frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', abs(data.received_qty + expected_qty))
    #                         frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', abs(data.total_qty- abs((expected_qty))))
    #                         received_qty += expected_qty
    #                         # Check status and update
    #                         if abs(data.total_qty - abs((expected_qty))) == 0:
    #                             frappe.db.set_value("Purchase Order Expected Date", data.name, 'status', 'Received')
    #                         else:
    #                             frappe.db.set_value("Purchase Order Expected Date", data.name, 'status', frappe.db.get_value("Purchase Order", data.purchase_order, 'workflow_state'))
    #                     else:
    #                         remaining_qty = total_qty - received_qty
    #                         frappe.db.set_value("Purchase Order Expected Date", data.name, 'total_qty', abs(data.total_qty-abs(remaining_qty)))
    #                         frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', abs(data.received_qty + remaining_qty))
    #                         frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', abs(data.total_qty-abs(remaining_qty)))
    #                         received_qty += remaining_qty
    #                         if abs(data.total_qty-abs(remaining_qty)) == 0:   
    #                             frappe.db.set_value("Purchase Order Expected Date", data.name, 'status', 'Received')
    #                         else:
    #                             frappe.db.set_value("Purchase Order Expected Date", data.name, 'status', frappe.db.get_value("Purchase Order", data.purchase_order, 'workflow_state'))
    #                     # Stop further processing if total received quantity is greater than or equal to total quantity
    #                     if received_qty >= total_qty:
    #                         break



@frappe.whitelist()
def update_cancel_purchase_order_expected_date(doc, method=None):
    if doc.workflow_state == 'Cancelled':
        for item in doc.items:
            if item.purchase_order:
                purchase_order_expected_list = frappe.db.get_list(
                    "Purchase Order Expected Date", 
                    filters={'item_code': item.item_code},
                    fields=['name', 'expected_qty', 'qty', 'received_qty', 'final_expected_receive_date','purchase_order'],
                    order_by='`tabPurchase Order Expected Date`.creation asc'
                )
                total_qty = item.qty
                canceled_qty = total_qty
                received_qty_to_cancel = canceled_qty
                for data in purchase_order_expected_list:
                    item_schedule_date = datetime.strptime(str(item.schedule_date), '%Y-%m-%d') if item.schedule_date else None
                    po_expected_date = datetime.strptime(str(data.final_expected_receive_date), '%Y-%m-%d') if data.final_expected_receive_date else None
                    if received_qty_to_cancel > 0:
                        # Handles scenarios where item schedule date is earlier, later, or matches the PO expected date
                        # Updates received_qty, expected_qty, and status for each record accordingly
                        # Check if the item schedule date matches the PO expected date and if the quantities match
                        if item_schedule_date == po_expected_date and item.qty == data.qty:
                            available_received_qty = data.received_qty
                            remaining_qty_to_deduct = min(available_received_qty, received_qty_to_cancel)
                            new_received_qty = data.received_qty - remaining_qty_to_deduct
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', new_received_qty)
                            new_expected_qty = data.qty - new_received_qty
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', new_expected_qty)
                            received_qty_to_cancel -= remaining_qty_to_deduct
                            if new_received_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                        # If the item schedule date is earlier than the PO expected date
                        elif item_schedule_date < po_expected_date:
                            available_received_qty = data.received_qty
                            remaining_qty_to_deduct = min(available_received_qty, received_qty_to_cancel)
                            new_received_qty = data.received_qty - remaining_qty_to_deduct
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', new_received_qty)
                            new_expected_qty = data.qty - new_received_qty
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', new_expected_qty)
                            received_qty_to_cancel -= remaining_qty_to_deduct
                            if new_received_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                        # If the item schedule date is later than the PO expected date
                        elif item_schedule_date > po_expected_date:
                            available_received_qty = data.received_qty
                            remaining_qty_to_deduct = min(available_received_qty, received_qty_to_cancel)
                            new_received_qty = data.received_qty - remaining_qty_to_deduct
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', new_received_qty)
                            new_expected_qty = data.qty - new_received_qty
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', new_expected_qty)
                            received_qty_to_cancel -= remaining_qty_to_deduct
                            if new_received_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                        # If the item schedule date matches the PO expected date but quantities are not equal
                        elif item_schedule_date == po_expected_date and item.qty!=data.qty:
                            available_received_qty = data.received_qty
                            remaining_qty_to_deduct = min(available_received_qty, received_qty_to_cancel)
                            new_received_qty = data.received_qty - remaining_qty_to_deduct
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', new_received_qty)
                            new_expected_qty = data.qty - new_received_qty
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', new_expected_qty)
                            received_qty_to_cancel -= remaining_qty_to_deduct
                            if new_received_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                    # If the total received quantity is greater than or equal to the total quantity, stop further processing 
                    if received_qty_to_cancel <= 0:
                        break
