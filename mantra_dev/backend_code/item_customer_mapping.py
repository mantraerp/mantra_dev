import frappe # type: ignore
from frappe import _ # type: ignore
from mantra_dev.backend_code.globle import errorLog,errorLogExites # type: ignore


# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.item_customer_mapping.enqueue_sales_order_mapping_job
@frappe.whitelist(allow_guest=True)
def enqueue_sales_order_mapping_job():
    frappe.enqueue(process_sales_order_mappings, queue="long", timeout=3600)
    return "Enqueued first job to process Sales Orders"

@frappe.whitelist()
def process_sales_order_mappings():
    try:
        sales_order_list = frappe.db.sql('''
            SELECT name, customer FROM `tabSales Order` WHERE docstatus = 1
        ''', as_dict=True)

        for so in sales_order_list:
            so["items"] = []
            so_items = frappe.get_doc("Sales Order", so.name)
            for j in so_items.items:
                if j.item_code not in so["items"]:
                    so["items"].append(j.item_code)

                default_bom = frappe.db.get_value(
                    "BOM",
                    {"item": j.item_code, "is_default": 1, "is_active": 1},
                    "name"
                )

                if default_bom:
                    bom_doc = frappe.get_doc("BOM", default_bom)
                    for k in bom_doc.items:
                        if k.item_code not in so["items"]:
                            so["items"].append(k.item_code)

        if sales_order_list:
            # Enqueue first SO with remaining list
            first = sales_order_list.pop(0)
            frappe.enqueue(
                create_item_customer_mapping_document,
                queue="long",
                timeout=3600,
                sales_order_single_entry=first,
                remaining_sales_orders=sales_order_list
            )
    except Exception:
        errorLog('Failed processing Sales Orders',str(frappe.get_traceback()),False)
        # frappe.log_error(frappe.get_traceback(), "Failed processing Sales Orders")
        


def create_item_customer_mapping_document(sales_order_single_entry, remaining_sales_orders=None):
    try:
        for item_code in sales_order_single_entry.get("items", []):
            try:
                mapping_exists = frappe.db.exists("Item Customer Mapping", item_code)
                if not mapping_exists:
                    doc = frappe.new_doc("Item Customer Mapping")
                    doc.item = item_code
                    doc.append("customer_and_reference", {
                        "customer": sales_order_single_entry.get("customer"),
                        "reference": sales_order_single_entry.get("name"),
                    })
                    doc.insert(ignore_permissions=True)
                else:
                    doc = frappe.get_doc("Item Customer Mapping", item_code)
                    existing = [d.customer for d in doc.customer_and_reference]
                    if sales_order_single_entry.get("customer") not in existing:
                        doc.append("customer_and_reference", {
                            "customer": sales_order_single_entry.get("customer"),
                            "reference": sales_order_single_entry.get("name"),
                        })
                        doc.save(ignore_permissions=True)
            except Exception:
                errorLog(f"Error in item mapping for item: {item_code}",str(frappe.get_traceback()),False)
                # frappe.log_error(frappe.get_traceback(), f"Error in item mapping for item: {item_code}")


        if remaining_sales_orders:
            next_so = remaining_sales_orders.pop(0)
            frappe.enqueue(
                create_item_customer_mapping_document,
                queue="long",
                timeout=3600,
                sales_order_single_entry=next_so,
                remaining_sales_orders=remaining_sales_orders
            )

    except Exception:
        errorLog(f"Error processing SO: {sales_order_single_entry.get('name')}",str(frappe.get_traceback()),False)
        # frappe.log_error(frappe.get_traceback(), f"Error processing SO: {sales_order_single_entry.get('name')}")

