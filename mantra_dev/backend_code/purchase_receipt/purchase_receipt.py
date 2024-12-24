import frappe
from datetime import datetime
from frappe.utils import flt

@frappe.whitelist()
def update_purchase_order_expected_date(doc, method=None):
    if doc.workflow_state == 'Approved':
        for item in doc.items:
            if item.purchase_order:
                # Fetches all the 'Purchase Order Expected Date' records related to the item code
                purchase_order_expected_list = frappe.db.get_list(
                    "Purchase Order Expected Date", 
                    filters={'item_code': item.item_code},
                    fields=['name', 'expected_qty', 'qty', 'received_qty', 'final_expected_receive_date','purchase_order'],
                    order_by='`tabPurchase Order Expected Date`.creation asc')
                total_qty = item.qty 
                received_qty = 0  
                for data in purchase_order_expected_list:
                    item_schedule_date = datetime.strptime(str(item.schedule_date), '%Y-%m-%d') if item.schedule_date else None
                    po_expected_date = datetime.strptime(str(data.final_expected_receive_date), '%Y-%m-%d') if data.final_expected_receive_date else None
                    # Check if the item schedule date matches the PO expected date and if the quantities match
                    if (item_schedule_date == po_expected_date and flt(item.qty) == flt(data.qty)):
                        expected_qty = data.expected_qty
                        # If the total received quantity + expected quantity is less than or equal to total_qty
                        if received_qty + expected_qty <= total_qty:
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', data.received_qty + expected_qty)
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', data.qty - (data.received_qty + expected_qty))
                            received_qty += expected_qty  
                            if data.received_qty + expected_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                       
                    # If the item schedule date is earlier than the PO expected date
                    elif item_schedule_date < po_expected_date:
                        expected_qty = data.expected_qty
                        if received_qty + expected_qty <= total_qty:
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', data.received_qty + expected_qty)
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', data.qty - (data.received_qty + expected_qty))
                            received_qty += expected_qty  
                            if data.received_qty + expected_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                        else:
                            remaining_qty = total_qty - received_qty
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', data.received_qty + remaining_qty)
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', data.qty - (data.received_qty + remaining_qty))
                            received_qty += remaining_qty
                            if data.received_qty + remaining_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                    # If the item schedule date is later than the PO expected date
                    elif item_schedule_date > po_expected_date:
                        expected_qty = data.expected_qty
                        if received_qty + expected_qty <= total_qty:
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', data.received_qty + expected_qty)
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', data.qty - (data.received_qty + expected_qty))
                            received_qty += expected_qty  
                            if data.received_qty + expected_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                        else:
                            remaining_qty = total_qty - received_qty
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', data.received_qty + remaining_qty)
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', data.qty - (data.received_qty + remaining_qty))
                            received_qty += remaining_qty
                            if data.received_qty + remaining_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                    #If the item schedule date matches the PO expected date but quantities are not equal
                    elif (item_schedule_date == po_expected_date and item.qty!=data.qty) or (item_schedule_date == po_expected_date and item.qty!=data.qty):
                        expected_qty = data.expected_qty
                        if received_qty + expected_qty <= total_qty:
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', data.received_qty + expected_qty)
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', data.qty - (data.received_qty + expected_qty))
                            received_qty += expected_qty  
                            if data.received_qty + expected_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                        else:
                            remaining_qty = total_qty - received_qty
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'received_qty', data.received_qty + remaining_qty)
                            frappe.db.set_value("Purchase Order Expected Date", data.name, 'expected_qty', data.qty - (data.received_qty + remaining_qty))
                            received_qty += remaining_qty
                            if data.received_qty + remaining_qty == data.qty:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status','Received')
                            else:
                                frappe.db.set_value("Purchase Order Expected Date", data.name, 'status',frappe.db.get_value("Purchase Order",data.purchase_order,'workflow_state'))
                    #If the total received quantity is greater than or equal to the total quantity, stop further processing
                    if received_qty >= total_qty:
                        break



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
