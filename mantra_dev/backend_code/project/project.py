import frappe # type: ignore
from collections import defaultdict

@frappe.whitelist()
def get_sales_order_items(project=None,sales_order=None,purchase_order=None):
    if not project and not sales_order and not purchase_order:
        return []
    if project:
        sales_orders = frappe.get_all('Sales Order', filters={'project': project,'docstatus':['!=',2]}, pluck='name')
    elif sales_order:
        sales_orders=[sales_order]
    item_data = {}

    warehouse_set = set()
    if not purchase_order:
        if not sales_orders:
            return []
    
        sales_order_items = frappe.get_all(
            'Sales Order Item',
            filters={'parent': ['in', sales_orders]},
            fields=['item_code', 'bom_no', 'qty','warehouse']
        )
        for item in sales_order_items:
            if item['warehouse']:
                warehouse_set.add(item['warehouse'])  
            key = (item['item_code'])  

            if key in item_data:
                item_data[key]['qty'] += item['qty']
            else:
                item_data[key] = {
                    'item': item['item_code'],
                    'bom': item['bom_no'] if item['bom_no'] else '',
                    'qty': item['qty']
                }
    else:

        purchase_order_items = frappe.get_all(
            'Purchase Order Item',
            filters={'parent': ['in', purchase_order]},
            fields=['item_code','qty','warehouse','bom']
        )
 

        for item in purchase_order_items:
            if item['warehouse']:
                warehouse_set.add(item['warehouse'])  
            key = (item['item_code'])  

            if key in item_data:
                item_data[key]['qty'] += item['qty']
            else:
                item_data[key] = {
                    'item': item['item_code'],
                    'bom': item['bom'] if item['bom'] else '',
                    'qty': item['qty']
                }
    aggregated_items = list(item_data.values())
    warehouse_list = list(warehouse_set)
    return aggregated_items , warehouse_list if len(warehouse_list) > 0 else []
