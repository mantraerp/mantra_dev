import frappe
from frappe import _


def get_context(context):
    """
    This function retrieves the query parameters from the URL and renders the HTML template
    with the provided details.
    """
    context.name = frappe.local.request.args.get('name')
    context.item_code = frappe.local.request.args.get('item_code')
    context.item_name = frappe.local.request.args.get('item_name')
    context.report_date = frappe.local.request.args.get('report_date')
    context.batch_no = frappe.local.request.args.get('batch_no')
    context.serial_no = frappe.local.request.args.get('serial_no')
    context.sample_size = frappe.local.request.args.get('sample_size')
    context.actual_qty = frappe.local.request.args.get('actual_qty')

    return context