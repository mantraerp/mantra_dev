from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Voucher Type"), "fieldname": "VoucherType", "fieldtype": "Data", "width": 150},
        {"label": _("Voucher Number"), "fieldname": "VoucherNumber", "fieldtype": "Data", "width": 150},
        {"label": _("Date"), "fieldname": "Date", "fieldtype": "Date", "width": 100},
        {"label": _("Supplier Inv No"), "fieldname": "SupplierInvNo", "fieldtype": "Data", "width": 150},
        {"label": _("Sup. Date"), "fieldname": "SupDate", "fieldtype": "Date", "width": 100},
        {"label": _("Party Name"), "fieldname": "PartyName", "fieldtype": "Data", "width": 150},
        {"label": _("Tracking"), "fieldname": "Tracking", "fieldtype": "Data", "width": 100},
        {"label": _("Receipt Date"), "fieldname": "ReceiptDate", "fieldtype": "Date", "width": 100},
        {"label": _("Receipt Doc no"), "fieldname": "ReceiptDocNo", "fieldtype": "Data", "width": 150},
        {"label": _("Dispatch Through"), "fieldname": "DispatchThrough", "fieldtype": "Data", "width": 150},
        {"label": _("Destination"), "fieldname": "Destination", "fieldtype": "Data", "width": 150},
        {"label": _("Carrier Name"), "fieldname": "CarrierName", "fieldtype": "Data", "width": 150},
        {"label": _("Bill of Lading"), "fieldname": "BillOfLading", "fieldtype": "Data", "width": 150},
        {"label": _("Bill of Landing Date"), "fieldname": "BillOfLandingDate", "fieldtype": "Date", "width": 150},
        {"label": _("Order No."), "fieldname": "OrderNo", "fieldtype": "Data", "width": 150},
        {"label": _("Order Date"), "fieldname": "OrderDate", "fieldtype": "Date", "width": 100},
        {"label": _("Terms of Payment"), "fieldname": "TermsOfPayment", "fieldtype": "Data", "width": 150},
        {"label": _("Supplier Name"), "fieldname": "SupplierName", "fieldtype": "Data", "width": 150},
        {"label": _("Address 1"), "fieldname": "Address1", "fieldtype": "Data", "width": 150},
        {"label": _("Address 2"), "fieldname": "Address2", "fieldtype": "Data", "width": 150},
        {"label": _("Address 3"), "fieldname": "Address3", "fieldtype": "Data", "width": 150},
        {"label": _("State"), "fieldname": "State", "fieldtype": "Data", "width": 100},
        {"label": _("Country"), "fieldname": "Country", "fieldtype": "Data", "width": 100},
        {"label": _("Pincode"), "fieldname": "Pincode", "fieldtype": "Data", "width": 100},
        {"label": _("GSTIN"), "fieldname": "GSTIN", "fieldtype": "Data", "width": 150},
        {"label": _("Buyers Name"), "fieldname": "BuyersName", "fieldtype": "Data", "width": 150},
        {"label": _("Buyers Address 1"), "fieldname": "BuyersAddress1", "fieldtype": "Data", "width": 150},
        {"label": _("Buyers Address 2"), "fieldname": "BuyersAddress2", "fieldtype": "Data", "width": 150},
        {"label": _("Buyers Address 3"), "fieldname": "BuyersAddress3", "fieldtype": "Data", "width": 150},
        {"label": _("Buyers State"), "fieldname": "BuyersState", "fieldtype": "Data", "width": 100},
        {"label": _("Buyers Country"), "fieldname": "BuyersCountry", "fieldtype": "Data", "width": 100},
        {"label": _("Buyers Pincode"), "fieldname": "BuyersPincode", "fieldtype": "Data", "width": 100},
        {"label": _("Buyers GSTIN"), "fieldname": "BuyersGSTIN", "fieldtype": "Data", "width": 150},
        {"label": _("Ledger Amount"), "fieldname": "LedgerAmount", "fieldtype": "Currency", "width": 150},
        {"label": _("Amount Type"), "fieldname": "AmountType", "fieldtype": "Data", "width": 100},
        {"label": _("New Ref"), "fieldname": "NewRef", "fieldtype": "Data", "width": 100},
        {"label": _("Ref Name"), "fieldname": "RefName", "fieldtype": "Data", "width": 150},
        {"label": _("PO Number"), "fieldname": "PONumber", "fieldtype": "Data", "width": 150},
        {"label": _("PO Date"), "fieldname": "PODate", "fieldtype": "Date", "width": 100},
        {"label": _("Due Date / Days"), "fieldname": "DueDateDays", "fieldtype": "Date", "width": 100},
        {"label": _("Amount"), "fieldname": "Amount", "fieldtype": "Currency", "width": 100},
        {"label": _("Purchase Ledger"), "fieldname": "PurchaseLedger", "fieldtype": "Data", "width": 150},
        {"label": _("Nature of Transaction"), "fieldname": "NatureOfTransaction", "fieldtype": "Data", "width": 150},
        {"label": _("Item Name"), "fieldname": "ItemName", "fieldtype": "Data", "width": 150},
        {"label": _("ItemDesc1"), "fieldname": "ItemDesc1", "fieldtype": "Data", "width": 150},
        {"label": _("ItemDesc2"), "fieldname": "ItemDesc2", "fieldtype": "Data", "width": 150},
        {"label": _("ItemDesc3"), "fieldname": "ItemDesc3", "fieldtype": "Data", "width": 150},
        {"label": _("Godown"), "fieldname": "Godown", "fieldtype": "Data", "width": 150},
        {"label": _("Actual Qty"), "fieldname": "ActualQty", "fieldtype": "Float", "width": 100},
        {"label": _("Billed Qty"), "fieldname": "BilledQty", "fieldtype": "Float", "width": 100},
        {"label": _("Discount"), "fieldname": "Discount", "fieldtype": "Currency", "width": 100},
        {"label": _("UOM"), "fieldname": "UOM", "fieldtype": "Data", "width": 100},
        {"label": _("Rate"), "fieldname": "Rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Amount"), "fieldname": "Amount", "fieldtype": "Currency", "width": 100},
        {"label": _("TaxName1"), "fieldname": "TaxName1", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate1"), "fieldname": "TaxRate1", "fieldtype": "Percent", "width": 100},
        {"label": _("TaxAmount1"), "fieldname": "TaxAmount1", "fieldtype": "Currency", "width": 100},
        {"label": _("TaxName2"), "fieldname": "TaxName2", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate2"), "fieldname": "TaxRate2", "fieldtype": "Percent", "width": 100},
        {"label": _("TaxAmount2"), "fieldname": "TaxAmount2", "fieldtype": "Currency", "width": 100},
        {"label": _("TaxName3"), "fieldname": "TaxName3", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate3"), "fieldname": "TaxRate3", "fieldtype": "Percent", "width": 100},
        {"label": _("TaxAmount3"), "fieldname": "TaxAmount3", "fieldtype": "Currency", "width": 100},
        {"label": _("TaxName4"), "fieldname": "TaxName4", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate4"), "fieldname": "TaxRate4", "fieldtype": "Percent", "width": 100},
        {"label": _("TaxAmount4"), "fieldname": "TaxAmount4", "fieldtype": "Currency", "width": 100},
        {"label": _("TaxName5"), "fieldname": "TaxName5", "fieldtype": "Data", "width": 150},
        {"label": _("TaxRate5"), "fieldname": "TaxRate5", "fieldtype": "Percent", "width": 100},
        {"label": _("TaxAmount5"), "fieldname": "TaxAmount5", "fieldtype": "Currency", "width": 100},
        {"label": _("Bill of entry no."), "fieldname": "BillOfEntryNo", "fieldtype": "Data", "width": 150},
        {"label": _("Bill of Entry Date"), "fieldname": "BillOfEntryDate", "fieldtype": "Date", "width": 100},
        {"label": _("Port code"), "fieldname": "PortCode", "fieldtype": "Data", "width": 100},
        {"label": _("Narration"), "fieldname": "Narration", "fieldtype": "Data", "width": 150},
        {"label": _("Department/Class"), "fieldname": "DepartmentClass", "fieldtype": "Data", "width": 150}
    ]

def get_data(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += "pi.posting_date BETWEEN '{0}' AND '{1}'".format(filters.get("from_date"), filters.get("to_date"))
    
    data = frappe.db.sql("""
        SELECT
            pi.custom_invoice_type AS VoucherType,
            pi.name AS VoucherNumber,
            pi.posting_date AS Date,
            pi.bill_no AS SupplierInvNo,
            pi.bill_date AS SupDate,
            pi.supplier_name AS PartyName,
            pii.purchase_receipt AS Tracking,
            pr.posting_date AS ReceiptDate,
            pii.purchase_receipt AS ReceiptDocNo,
            ' ' AS DispatchThrough,
            ' ' AS Destination,
            ' ' AS CarrierName,
            ' ' AS BillOfLading,
            ' ' AS BillOfLandingDate,
            pii.purchase_order AS OrderNo,
            po.transaction_date AS OrderDate,
            pi.payment_terms_template AS TermsOfPayment,
            pi.supplier_name AS SupplierName,
            sa.address_line1 AS Address1,
            sa.address_line2 AS Address2,
            sa.city AS Address3,
            sa.state AS State,
            sa.country AS Country,
            sa.pincode AS Pincode,
            sa.gstin AS GSTIN,
            pi.company AS BuyersName,
            ca.address_line1 AS BuyersAddress1,
            ca.address_line2 AS BuyersAddress2,
            ca.city AS BuyersAddress3,
            ca.state AS BuyersState,
            ca.country AS BuyersCountry,
            ca.pincode AS BuyersPincode,
            ca.gstin AS BuyersGSTIN,
            pi.base_grand_total AS LedgerAmount,
            'CR' AS AmountType,
            'New Ref' AS NewRef,
            pi.bill_no AS RefName,
            pii.purchase_order AS PONumber,
            po.transaction_date AS PODate,
            pi.due_date AS DueDateDays,
            pi.base_total AS Amount,
            pii.expense_account AS PurchaseLedger,
            pi.taxes_and_charges AS NatureOfTransaction,
            CONCAT(pii.item_code, ' ', pii.item_name) AS ItemName,
            pii.custom_item_description AS ItemDesc1,
            pii.custom_note AS ItemDesc2,
            ' ' AS ItemDesc3,
            pii.warehouse AS Godown,
            pii.qty AS ActualQty,
            pii.qty AS BilledQty,
            pii.discount_amount AS Discount,
            pii.uom AS UOM,
            pii.rate AS Rate,
            pii.base_amount AS Amount,
            'Input CGST' AS TaxName1,
            pii.cgst_rate AS TaxRate1,
            pii.cgst_amount AS TaxAmount1,
            'Input SGST' AS TaxName2,
            pii.sgst_rate AS TaxRate2,
            pii.sgst_amount AS TaxAmount2,
            'Input IGST' AS TaxName3,
            pii.igst_rate AS TaxRate3,
            pii.igst_amount AS TaxAmount3,
            pt.account_head AS TaxName4,
            pt.rate AS TaxRate4,
            pt.tax_amount AS TaxAmount4,
            ' ' AS TaxName5,
            ' ' AS TaxRate5,
            ' ' AS TaxAmount5,
            be.name AS BillOfEntryNo,
            be.bill_of_entry_date AS BillOfEntryDate,
            be.port_code AS PortCode,
            pi.custom_narration AS Narration,
            pi.cost_center AS DepartmentClass
        FROM
            `tabPurchase Invoice` pi
        JOIN
            `tabPurchase Invoice Item` AS pii ON pii.parent = pi.name
        LEFT JOIN
            `tabPurchase Order` AS po ON pii.purchase_order = po.name
        LEFT JOIN
            `tabPurchase Receipt` AS pr ON pr.name = pii.purchase_receipt
        LEFT JOIN
            `tabAddress` AS sa ON sa.name = pi.supplier_address
        LEFT JOIN
            `tabAddress` AS ca ON ca.name = pi.billing_address
        LEFT JOIN
            `tabBill of Entry` AS be ON be.purchase_invoice = pi.name
        LEFT JOIN
            `tabPurchase Taxes and Charges` AS pt ON pt.parent = pi.name
        WHERE
            pi.docstatus = 1 AND {conditions}
        ORDER BY
            pii.parent
    """.format(conditions=conditions), as_dict=True)

    return data
