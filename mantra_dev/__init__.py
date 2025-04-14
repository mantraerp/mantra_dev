__version__ = "0.0.1"
import erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry # type: ignore
# import mantra_dev.backend_code.stock_reservation_entry
import mantra_dev.backend_code.stock_reservation_entry.stock_reservation_entry # type: ignore

import erpnext.accounts.doctype.purchase_invoice.purchase_invoice # type: ignore
import mantra_dev.purchase_invoice # type: ignore

import erpnext.stock.doctype.purchase_receipt.purchase_receipt # type: ignore
import mantra_dev.purchase_receipt # type: ignore

import erpnext.stock.doctype.shipment.shipment # type: ignore
import mantra_dev.backend_code.shipment.shipment # type: ignore

import erpnext.selling.doctype.sales_order.sales_order # type: ignore
import mantra_dev.backend_code.sales_order.sales_order # type: ignore

import erpnext.accounts.doctype.sales_invoice.sales_invoice # type: ignore
import mantra_dev.backend_code.sales_invoice.sales_invoice # type: ignore

import erpnext.accounts.doctype.bank_account.bank_account # type: ignore
import mantra_dev.backend_code.bank_account.bank_account # type: ignore

from erpnext.controllers.accounts_controller import AccountsController # type: ignore
import mantra_dev.backend_code.accounts_controller # type: ignore




erpnext.accounts.doctype.sales_invoice.sales_invoice.make_delivery_note = mantra_dev.backend_code.sales_invoice.sales_invoice.make_delivery_note

erpnext.accounts.doctype.bank_account.bank_account.BankAccount.on_trash = mantra_dev.backend_code.bank_account.bank_account.BankAccount.on_trash


erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry.create_stock_reservation_entries_for_so_items = mantra_dev.backend_code.stock_reservation_entry.stock_reservation_entry.create_stock_reservation_entries_for_so_items

erpnext.accounts.doctype.purchase_invoice.purchase_invoice.PurchaseInvoice.po_required = mantra_dev.purchase_invoice.PurchaseInvoice.po_required

erpnext.accounts.doctype.purchase_invoice.purchase_invoice.PurchaseInvoice.pr_required = mantra_dev.purchase_invoice.PurchaseInvoice.pr_required

erpnext.stock.doctype.purchase_receipt.purchase_receipt.PurchaseReceipt.po_required = mantra_dev.purchase_invoice.PurchaseInvoice.po_required

erpnext.stock.doctype.shipment.shipment.Shipment.on_submit = mantra_dev.backend_code.shipment.shipment.Shipment.on_submit

erpnext.selling.doctype.sales_order.sales_order.make_raw_material_request = mantra_dev.backend_code.sales_order.sales_order.make_raw_material_request

erpnext.controllers.accounts_controller.AccountsController.set_due_date = mantra_dev.backend_code.accounts_controller.set_due_date