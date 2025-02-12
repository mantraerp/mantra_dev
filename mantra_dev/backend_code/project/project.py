import frappe # type: ignore
from collections import defaultdict

@frappe.whitelist()
def get_sales_order_items(project):
    if not project:
        return []
    sales_orders = frappe.get_all('Sales Order', filters={'project': project,'docstatus':['!=',2]}, pluck='name')
    if not sales_orders:
        return []
    sales_order_items = frappe.get_all(
        'Sales Order Item',
        filters={'parent': ['in', sales_orders]},
        fields=['item_code', 'bom_no', 'qty','warehouse']
    )
    item_data = {}

    warehouse_set = set()

    for item in sales_order_items:
        if item['warehouse']:
            warehouse_set.add(item['warehouse'])  
        key = (item['item_code'], item['bom_no'])  

        if key in item_data:
            item_data[key]['qty'] += item['qty']
        else:
            item_data[key] = {
                'item': item['item_code'],
                'bom': item['bom_no'],
                'qty': item['qty']
            }
    aggregated_items = list(item_data.values())
    warehouse_list = list(warehouse_set)
    return aggregated_items , warehouse_list if len(warehouse_list) > 0 else []
