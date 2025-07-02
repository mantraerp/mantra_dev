import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"fieldname": "sales_order", "label": _("Sales Order"), "fieldtype": "Link", "options": "Sales Order", "width": 150},
        {"fieldname": "sales_invoice", "label": _("Sales Invoice"), "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"fieldname": "delivery_note", "label": _("Delivery Note"), "fieldtype": "Link", "options": "Delivery Note", "width": 150},
        {"fieldname": "serial_and_batch_bundle", "label": _("Serial and Batch Bundle"), "fieldtype": "Link", "options": "Serial and Batch Bundle", "width": 150},
        {"fieldname": "warehouse", "label": _("Warehouse"), "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"fieldname": "shipment", "label": _("Shipment"), "fieldtype": "Link", "options": "Shipment", "width": 150},
        {"fieldname": "service_provider", "label": _("Service Provider"), "fieldtype": "Data", "width": 150},
        {"fieldname": "awb_number", "label": _("AWB Number"), "fieldtype": "Data", "width": 150}
    ]

    conditions = "d.docstatus = 1"
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND d.posting_date BETWEEN %(from_date)s AND %(to_date)s"

    # Use Query Builder
    data = frappe.get_all(
        "Delivery Note Item",
        fields=[
            "against_sales_order as sales_order",
            "against_sales_invoice as sales_invoice",
            "parent as delivery_note",
            "serial_and_batch_bundle as serial_and_batch_bundle",
            "warehouse as warehouse"
        ],
        filters={
            "parent": ["in", frappe.get_all("Delivery Note", fields=["name"], filters={"docstatus": 1, "posting_date": ["between", [filters.get("from_date"), filters.get("to_date")]]})]
        },
        join=[
            {"table": "tabSerial and Batch Entry", "condition": "tabSerial and Batch Entry.parent = `tabDelivery Note Item`.serial_and_batch_bundle", "type": "LEFT"},
            {"table": "tabShipment Delivery Note", "condition": "tabShipment Delivery Note.delivery_note = `tabDelivery Note`.name", "type": "LEFT"},
            {"table": "tabShipment", "condition": "tabShipment.name = tabShipment Delivery Note.parent", "type": "LEFT"}
        ],
        additional_fields=[
            "tabShipment.service_provider as service_provider",
            "tabShipment.awb_number as awb_number"
        ],
        order_by="against_sales_order"
    )

    return columns, data
