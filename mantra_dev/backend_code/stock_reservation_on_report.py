from typing import Literal
import json
import frappe
from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import create_stock_reservation_entries_for_so_items
from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import cancel_stock_reservation_entries
@frappe.whitelist()
# def create_stock_reservation_entry(values: str) -> None:
def create_stock_reservation_entries(values, doc, from_voucher_type: Literal["Pick List", "Purchase Receipt"] = None, notify=True):
    values = json.loads(values)
    print(values)
    print(values[0]["qty_to_reserve"])
   
    doc = frappe.get_doc("Sales Order", doc)    
    create_stock_reservation_entries_for_so_items(
        sales_order=doc,
        items_details=values,
        from_voucher_type=from_voucher_type,
        notify=notify,
    )      
@frappe.whitelist()
def cancel_stock_reservation_entrie(doc, sre_list=None, notify=True) -> None:
    """Cancel Stock Reservation Entries for Sales Order Items."""

    print(sre_list)
    # src_list_str = '"MAT-SRE-2024-00049","MAT-SRE-2024-00054"'
    # src_list = sre_list.strip('')
    list_with_quotes = sre_list.strip('[]').split(',')
    list_with_quotes = [item.strip('" ').strip("'") for item in list_with_quotes]

    # src_list = src_list_li.strip(',')
    print(type(list_with_quotes))
    print(list_with_quotes)
    cancel_stock_reservation_entries(sre_list=list_with_quotes, notify=notify)
