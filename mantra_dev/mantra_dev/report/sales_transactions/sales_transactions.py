from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Voucher Number"), "fieldname": "voucher_number", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Party Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 200},
        {"label": _("Delivery Note No"), "fieldname": "delivery_note_no", "fieldtype": "Link", "options": "Delivery Note", "width": 150},
        {"label": _("Delivery Note Date"), "fieldname": "delivery_note_date", "fieldtype": "Date", "width": 100},
        {"label": _("Dispatch doc no."), "fieldname": "dispatch_doc_no", "fieldtype": "Link", "options": "Shipment", "width": 150},
        {"label": _("Dispatch Through"), "fieldname": "dispatch_through", "fieldtype": "Data", "width": 150},
        {"label": _("Destination"), "fieldname": "destination", "fieldtype": "Data", "width": 150},
        {"label": _("Carrier Name"), "fieldname": "carrier_name", "fieldtype": "Data", "width": 150},
        {"label": _("Pick up Date"), "fieldname": "pick_up_date", "fieldtype": "Date", "width": 100},
        {"label": _("Order No"), "fieldname": "order_no", "fieldtype": "Link", "options": "Sales Order", "width": 150},
        {"label": _("Order Date"), "fieldname": "order_date", "fieldtype": "Date", "width": 100},
        {"label": _("Terms of Payment"), "fieldname": "terms_of_payment", "fieldtype": "Data", "width": 150},
        {"label": _("Buyers Name"), "fieldname": "buyers_name", "fieldtype": "Data", "width": 200},
        {"label": _("Buyers Address-1"), "fieldname": "buyers_address_1", "fieldtype": "Data", "width": 200},
        {"label": _("Buyers Address-2"), "fieldname": "buyers_address_2", "fieldtype": "Data", "width": 200},
        {"label": _("Buyers Address-3"), "fieldname": "buyers_address_3", "fieldtype": "Data", "width": 200},
        {"label": _("Buyers State"), "fieldname": "buyers_state", "fieldtype": "Data", "width": 100},
        {"label": _("Buyers Country"), "fieldname": "buyers_country", "fieldtype": "Data", "width": 100},
        {"label": _("Pin Code"), "fieldname": "pin_code", "fieldtype": "Data", "width": 100},
        {"label": _("Buyers GSTIN"), "fieldname": "buyers_gstin", "fieldtype": "Data", "width": 150},
        {"label": _("Buyers Place Of Supply"), "fieldname": "buyers_place_of_supply", "fieldtype": "Data", "width": 150},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Float", "width": 100},
        {"label": _("New Ref"), "fieldname": "new_ref", "fieldtype": "Data", "width": 100},
        {"label": _("Ref Name"), "fieldname": "ref_name", "fieldtype": "Data", "width": 150},
        {"label": _("PO No"), "fieldname": "po_no", "fieldtype": "Data", "width": 150},
        {"label": _("PO Date"), "fieldname": "po_date", "fieldtype": "Date", "width": 100},
        {"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 100},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 150},
        {"label": _("ItemDesc1"), "fieldname": "item_desc1", "fieldtype": "Data", "width": 200},
        {"label": _("ItemDesc2"), "fieldname": "item_desc2", "fieldtype": "Data", "width": 200},
        {"label": _("ItemDesc3"), "fieldname": "item_desc3", "fieldtype": "Data", "width": 200},
        {"label": _("Godown"), "fieldname": "godown", "fieldtype": "Data", "width": 150},
        {"label": _("Actual Qty"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Billed Qty"), "fieldname": "billed_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Per"), "fieldname": "per", "fieldtype": "Data", "width": 100},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Float", "width": 100},
        {"label": _("Discount"), "fieldname": "discount", "fieldtype": "Float", "width": 100},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Float", "width": 100},
        {"label": _("Consignee Address-1"), "fieldname": "consignee_address_1", "fieldtype": "Data", "width": 200},
        {"label": _("Consignee Address-2"), "fieldname": "consignee_address_2", "fieldtype": "Data", "width": 200},
        {"label": _("Consignee Address-3"), "fieldname": "consignee_address_3", "fieldtype": "Data", "width": 200},
        {"label": _("Consignee State"), "fieldname": "consignee_state", "fieldtype": "Data", "width": 100},
        {"label": _("Consignee Country"), "fieldname": "consignee_country", "fieldtype": "Data", "width": 100},
        {"label": _("Consignee Pincode"), "fieldname": "consignee_pincode", "fieldtype": "Data", "width": 100},
        {"label": _("TaxName1"), "fieldname": "tax_name1", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate1"), "fieldname": "tax_rate1", "fieldtype": "Float", "width": 100},
        {"label": _("TaxAmount1"), "fieldname": "tax_amount1", "fieldtype": "Float", "width": 100},
        {"label": _("TaxName2"), "fieldname": "tax_name2", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate2"), "fieldname": "tax_rate2", "fieldtype": "Float", "width": 100},
        {"label": _("TaxAmount2"), "fieldname": "tax_amount2", "fieldtype": "Float", "width": 100},
        {"label": _("TaxName3"), "fieldname": "tax_name3", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate3"), "fieldname": "tax_rate3", "fieldtype": "Float", "width": 100},
        {"label": _("TaxAmount3"), "fieldname": "tax_amount3", "fieldtype": "Float", "width": 100},
        {"label": _("TaxName4"), "fieldname": "tax_name4", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate4"), "fieldname": "tax_rate4", "fieldtype": "Float", "width": 100},
        {"label": _("TaxAmount4"), "fieldname": "tax_amount4", "fieldtype": "Float", "width": 100},
        {"label": _("TaxName5"), "fieldname": "tax_name5", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate5"), "fieldname": "tax_rate5", "fieldtype": "Float", "width": 100},
        {"label": _("TaxAmount5"), "fieldname": "tax_amount5", "fieldtype": "Float", "width": 100},
        {"label": _("Tax ledger"), "fieldname": "tax_ledger", "fieldtype": "Link", "options": "Account", "width": 150},
        {"label": _("Sales Man"), "fieldname": "sales_man", "fieldtype": "Data", "width": 150},
        {"label": _("ACK No"), "fieldname": "ack_no", "fieldtype": "Data", "width": 150},
        {"label": _("ACK Date"), "fieldname": "ack_date", "fieldtype": "Date", "width": 100},
        {"label": _("IRN"), "fieldname": "irn", "fieldtype": "Data", "width": 150},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Cost Center", "width": 150}
    ]

def get_data(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions = "si.posting_date BETWEEN '{0}' AND '{1}'".format(filters.get("from_date"), filters.get("to_date"))

    data = frappe.db.sql("""
        SELECT
            si.name AS voucher_number,
            si.posting_date AS date,
            si.customer_name AS party_name,
            dn.name AS delivery_note_no,
            dn.posting_date AS delivery_note_date,
            sh.name AS dispatch_doc_no,
            sh.service_provider AS dispatch_through,
            sh.delivery_address AS destination,
            sh.carrier_service AS carrier_name,
            sh.pickup_date AS pick_up_date,
            so.name AS order_no,
            so.transaction_date AS order_date,
            ps.description AS terms_of_payment,
            si.customer_name AS buyers_name,
            ba.address_line1 AS buyers_address_1,
            ba.address_line2 AS buyers_address_2,
            ba.city AS buyers_address_3,
            ba.state AS buyers_state,
            ba.country AS buyers_country,
            ba.pincode AS pin_code,
            si.billing_address_gstin AS buyers_gstin,
            si.place_of_supply AS buyers_place_of_supply,
            si.grand_total AS amount,
            1 AS new_ref,
            si.name AS ref_name,
            si.po_no AS po_no,
            si.po_date AS po_date,
            si.due_date AS due_date,
            sii.item_name AS item_name,
            si.cost_center AS cost_center,
            sii.custom_item_description AS item_desc1,
            NULL AS item_desc2,
            NULL AS item_desc3,
            sii.warehouse AS godown,
            sii.qty AS actual_qty,
            sii.qty AS billed_qty,
            sii.uom AS per,
            sii.rate AS rate,
            si.discount_amount AS discount,
            sii.amount AS amount,
            sa.address_line1 AS consignee_address_1,
            sa.address_line2 AS consignee_address_2,
            sa.city AS consignee_address_3,
            sa.state AS consignee_state,
            sa.country AS consignee_country,
            sa.pincode AS consignee_pincode,
            stc.account_head AS tax_name1,
            stc.rate AS tax_rate1,
            NULL AS tax_amount1,
            NULL AS tax_name2,
            NULL AS tax_rate2,
            NULL AS tax_amount2,
            NULL AS tax_name3,
            NULL AS tax_rate3,
            NULL AS tax_amount3,
            NULL AS tax_name4,
            NULL AS tax_rate4,
            NULL AS tax_amount4,
            NULL AS tax_name5,
            NULL AS tax_rate5,
            NULL AS tax_amount5,
            NULL AS tax_ledger,
            si.custom_sales_person AS sales_man,
            ei.acknowledgement_number AS ack_no,
            ei.acknowledged_on AS ack_date,
            ei.irn AS irn,
            si.cost_center AS department
        FROM `tabSales Invoice` AS si
        JOIN `tabSales Invoice Item` AS sii ON sii.parent = si.name
        JOIN `tabSales Order` AS so ON so.name = sii.sales_order
        LEFT JOIN `tabAddress` AS ba ON ba.name = si.customer_address
        LEFT JOIN `tabAddress` AS sa ON sa.name = si.shipping_address_name
        LEFT JOIN `tabDelivery Note Item` AS dni ON dni.against_sales_invoice = si.name
        LEFT JOIN `tabDelivery Note` AS dn ON dn.name = dni.parent
        LEFT JOIN `tabShipment Delivery Note` AS shd ON shd.delivery_note = dn.name
        LEFT JOIN `tabShipment` AS sh ON sh.name = shd.parent
        LEFT JOIN `tabPayment Schedule` AS ps ON ps.parent = si.name
        LEFT JOIN `tabSales Taxes and Charges` AS stc ON stc.parent = si.name
        LEFT JOIN `tabe-Invoice Log` AS ei ON ei.sales_invoice = si.name
        WHERE si.docstatus = 1
          AND si.status != 'Cancelled'
          AND {conditions}
        GROUP BY si.name, sii.item_code, sii.name
        ORDER BY si.creation DESC
    """.format(conditions=conditions), as_dict=True)

    return data
