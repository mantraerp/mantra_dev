import frappe # type: ignore
from frappe.utils import fmt_money # type: ignore

# This function creates a "Purchase Order Expected Date" record for each item in the purchase order
# when the purchase order is approved (workflow_state is 'Approved')
@frappe.whitelist()
def create_purchase_order_expected_date(doc,method=None):
    if doc.workflow_state == 'Approved':
        for item in doc.items:
            purchase_order = frappe.new_doc("Purchase Order Expected Date")
            purchase_order.purchase_order = doc.name
            purchase_order.item_code = item.item_code
            purchase_order.qty = item.qty
            purchase_order.expected_qty = item.qty
            purchase_order.total_qty = item.qty
            purchase_order.schedule_date = item.schedule_date
            purchase_order.expected_delivery_date = item.schedule_date
            purchase_order.status=doc.workflow_state 
            purchase_order.final_expected_receive_date = item.schedule_date
            purchase_order.insert(ignore_permissions=True)

# This function cancels or updates the status of "Purchase Order Expected Date" records
# when the workflow state of the associated purchase order changes.
@frappe.whitelist()
def cancel_purchase_order_expected_date(doc,method=None):
        purchase_order_names = frappe.db.get_list("Purchase Order Expected Date", filters={'purchase_order': doc.name}, pluck='name',ignore_permissions=True)
        if purchase_order_names:
            frappe.db.set_value(
                "Purchase Order Expected Date", 
                purchase_order_names, 
                "status", 
                doc.workflow_state
            )


@frappe.whitelist()
def get_stock_details(item_code, warehouse=None):
    """
    Fetch available stock quantity for an item in a given warehouse
    and total stock across all warehouses.
    """
    stock_data = {"available_qty_in_target": 0, "total_available_stock": 0}

    # Fetch available qty in the specified warehouse
    if warehouse:
        stock_data["available_qty_in_target"] = frappe.db.get_value(
            "Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"
        ) or 0

    # Fetch total available stock across all warehouses
    total_stock = frappe.db.sql(
        """SELECT SUM(actual_qty) FROM `tabBin` WHERE item_code=%s""",
        (item_code,),
    )
    stock_data["total_available_stock"] = total_stock[0][0] if total_stock and total_stock[0][0] else 0

    return stock_data


@frappe.whitelist()
def get_po_form_details(purchase_order_id):
    if frappe.db.exists("PO Form Approval", {'purchase_order': purchase_order_id, 'docstatus': 1}):
        doc = frappe.get_doc("PO Form Approval", {'purchase_order': purchase_order_id, 'docstatus': 1})
        return doc
    else:
        return None
    

# @frappe.whitelist()
# def make_po_form_approval(source_name, target_doc=None, ignore_permissions=False):
#     def postprocess(source, target):
#         set_missing_values(source, target)

#     def set_missing_values(source, target):
#         target.flags.ignore_permissions = True
#         target.append('price_comparison', {
#             'supplier_name': source.supplier_name,
#             'payment_terms': frappe.db.get_value("Supplier", source.supplier, "payment_terms") or ''
#         })
    
#     def update_item(source, target, source_parent):
#         stock_details = get_stock_details(source.item_code, source.warehouse or None)
#         target.target_warehouse_qty = stock_details['available_qty_in_target']
#         target.current_stock = stock_details['total_available_stock']
#         target.demand = 0
#         if source.material_request:
#             target.demand += frappe.db.get_value("Material Request Item", {'parent': source.material_request, 'docstatus': ['<', 2], 'item_code': source.item_code}, 'qty')
            
#     doclist = get_mapped_doc(
# 		"Purchase Order",
# 		source_name,
# 		{
# 			"Purchase Order": {
# 				"doctype": "PO Form Approval",
# 				"field_map": {
# 					"purchase_order": "name",
# 					"cost_center": "cost_center",
# 				},
# 			},
#             "Purchase Order Item": {
# 				"doctype": "PO Form Item Stock",
# 				"field_map": {
# 					"item_code": "item",
# 				},
# 				"postprocess": update_item,
# 				"condition": lambda doc: doc.qty
# 				and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
# 			},
# 		},
# 		target_doc,
#         postprocess,
# 		ignore_permissions=ignore_permissions,
# 	)

#     return doclist



def get_linked_purchase_order(pi_name):
    """
    Find the Purchase Order that created this Purchase Invoice.
    """
    po_list = frappe.db.sql("""
        SELECT DISTINCT purchase_order 
        FROM `tabPurchase Invoice Item`
        WHERE purchase_order IS NOT NULL 
        AND parent=%s
    """, (pi_name,), as_dict=True)

    return po_list[0]['purchase_order'] if po_list else None

def get_document_details(doctype, docname):
    """
    Fetch document details dynamically based on the doctype and document name.
    """
    if not frappe.db.exists(doctype, docname):
        return {"error": "Document not found"}
    
    doc = frappe.get_doc(doctype, docname)
    response = {"items": []}
    
    if doctype in ["Purchase Order", "Purchase Invoice", "Payment Request"]:
        po_id = None

        if doctype == "Payment Request":
            if doc.get("reference_doctype") == "Purchase Invoice":
                po_id = get_linked_purchase_order(doc.reference_name)
            else:
                po_id = doc.reference_name
        elif doctype == "Purchase Invoice":
            po_id = get_linked_purchase_order(docname)
        elif doctype == "Purchase Order":
            po_id = docname

        if po_id:
            po_doc = frappe.get_doc("Purchase Order", po_id)
            response.update({
                "po_form_details": get_po_form_details(po_id),
                "name": po_id,
                "status": frappe.db.get_value("Purchase Order", po_id, "status"),
                "grand_total": frappe.db.get_value("Purchase Order", po_id, "grand_total"),
                "supplier_name": frappe.db.get_value("Purchase Order", po_id, "supplier_name")
            })
            response["items"] = [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty,
                    "is_maintain_stock":frappe.db.get_value("Item",item.item_code,'is_stock_item'),
                    "rate": item.rate,
                    **get_stock_details(item.item_code, getattr(item, "warehouse", None))
                }
                for item in po_doc.items
            ]
        else:
            return
    
    return response



def generate_html(details):
    if not details:
        return "This document does not have an associated purchase order."
    """
    Generate HTML content from document details.
    """
    styles = """
    <style>
        .po-form-approval td div, .item-stock td div {
            text-align: left !important;
        }
        .po-form-approval td {
            width: 14.29%;
        }
     
    </style>
    """
    po_details_html = f"""
     {styles}
    <h4>{details.get('name', '')}</h4>
    <table class='table table-bordered item-stock'>
        <tbody>
            <tr>
                <td style="text-align:left;">Supplier Name:</td>
                <td style="text-align:left;">{details.get('supplier_name', '')}</td>
            </tr>
            <tr>
                <td style="text-align:left;">Status:</td>
                <td style="text-align:left;">{details.get('status', '')}</td>
            </tr>
            <tr>
                <td style="text-align:left;">Grand Total:</td>
                <td style="text-align:left;">{details.get('grand_total', '')}</td>
            </tr>
        </tbody>
    </table>
    """

    if details.get("items"):
        po_details_html += """
        <h5>Items:</h5>
        <table class='table table-bordered item-stock'>
            <thead>
                <tr>
                    <th style="text-align:left;">Item Name</th>
                    <th style="text-align:left;">Maintain Stock</th>
                    <th style="text-align:left;">Qty</th>
                    <th style="text-align:left;">Rate</th>
                    <th style="text-align:left;">Target Warehouse Qty</th>
                    <th style="text-align:left;">Total Stock</th>
                </tr>
            </thead>
            <tbody>
        """

        for item in details["items"]:
            checked = "checked" if item.get('is_maintain_stock') == 1 else ""
            po_details_html += f"""
                <tr>
                    <td width="28%" style="text-align:left;">{item['item_name']}</td>
                    <td width="12%" style="text-align:center;">
                     <input type="checkbox" {checked} disabled>
                    </td>
                    <td width="10%" style="text-align:left;">{float(item['qty']):.0f}</td>
                    <td width="10%" style="text-align:left;">{float(item['rate']):.0f}</td>
                    <td width="20%" style="text-align:left;">{float(item['available_qty_in_target']):.0f}</td>
                    <td width="20%" style="text-align:left;">{float(item['total_available_stock']):.0f}</td>
                </tr>
            """

        po_details_html += "</tbody></table>"

    po_approval_details = details.get("po_form_details", {})
    approval_link_html = ""
    final_supplier_quotation_link = ""
    nda = ""
    if po_approval_details:
        if po_approval_details.get("approval_link"):

            approval_link_html = f"""
            <button style='padding: 5px 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;' 
                onclick="window.open('{po_approval_details.get('approval_link')}', '_blank')">
                View Approval
            </button>
            """
        if po_approval_details.get("final_supplier_quotation_link"):
            final_supplier_quotation_link = f"""
            <button style='padding: 5px 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;' 
                onclick="window.open('{po_approval_details.get('final_supplier_quotation_link')}', '_blank')">
                 View Quotation
            </button>
            """

        if po_approval_details.get("nda"):

            nda = f"""<button style='padding: 5px 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;' 
                onclick="window.open('{po_approval_details.get('nda')}', '_blank')">
                 NDA
            </button>
"""
        po_approval_html = f"""
        <h4>PO Form Approval Details:</h4>
        <table class='table table-bordered po-form-approval'>
            <tbody>
                <tr>
                    <td style="text-align:left;">Project Code:</td>
                    <td style="text-align:left;" colspan='2'>{po_approval_details.get('project') or ''}</td>
                    <td style="text-align:left;">Project Name:</td>
                    <td style="text-align:left;" colspan='3'>{po_approval_details.get('project_name') or ''}</td>
                </tr>
                <tr>
                    <td style="text-align:left;">Sales Order No:</td>
                    <td style="text-align:left;" colspan='2'>{po_approval_details.get('sales_order') or ''}</td>
                    <td style="text-align:left;">Customer PO No:</td>
                    <td style="text-align:left;" colspan='3'>{po_approval_details.get('po_no') or ''}</td>
                </tr>
                 <tr>
                    <td style="text-align:left">Customer Code:</td>
                    <td style="text-align:left" colspan="2">{po_approval_details.get('customer') or ''}</td>
                    <td style="text-align:left">Customer Name:</td>
                    <td style="text-align:left" colspan="3">{po_approval_details.get('customer_name') or ''}</td>
                </tr>
                 <tr>
                    <td style="text-align:left">Business Unit Name:</td>
                    <td style="text-align:left" colspan="2">{po_approval_details.get('business_unit_name') or ''}</td>
                    <td style="text-align:left">Business Unit Email:</td>
                    <td style="text-align:left" colspan="3">{po_approval_details.get(
                        'business_unit_email') or ''}</td>
                </tr>
                 <tr>
                    <td style="text-align:left">Purpose:</td>
                    <td style="text-align:left" colspan="6">{po_approval_details.get('purpose') or ''}</td>
                </tr>
                <tr>
                    <td style="text-align:left">Cost Center/Profit Center:</td>
                    <td style="text-align:left" colspan="6">{po_approval_details.get('cost_center') or ''}</td>
                </tr>
                <tr>
                    <td style="text-align:left">Requester:</td>
                    <td style="text-align:left" colspan="2">{po_approval_details.get('requester') or ''}</td>
                    <td style="text-align:left">Approved By:</td>
                    <td style="text-align:left" colspan="3">{po_approval_details.get('approved_by') or ''}</td>
                </tr>
                  <tr>
                    <td style="text-align:left">Material Request:</td>
                    <td style="text-align:left" colspan="2">{po_approval_details.get(
                        'material_request') or ''}</td>
                    <td style="text-align:left">Request By:</td>
                    <td style="text-align:left" colspan="3">{po_approval_details.get('request_by') or ''}</td>
                </tr>
                <tr>
                    <td style="text-align:left">Approval Link:</td>
                    <td style="text-align:left" colspan="6">
                       {approval_link_html or ''}
                    </td>
                </tr>
                <tr>
                    <td style="text-align:left">Overall Profit in case if Project:</td>
                    <td style="text-align:left" colspan="6">{fmt_money(po_approval_details.get('overall_profit_in_case_if_project'),currency='INR') or fmt_money(0,currency='INR')}</td>
                </tr>
                  <tr>
                    <td style="text-align:left">Last Lowest Price:</td>
                    <td style="text-align:left" colspan="6">{fmt_money(po_approval_details.get('last_lowest_price'),currency='INR') or fmt_money(0,currency='INR')}</td>
                </tr>
                 <tr>
                    <td style="text-align:left">Final Supplier Quotation Link:</td>
                    <td style="text-align:left" colspan="6">
                       {final_supplier_quotation_link or ''}
                    </td>
                </tr>
                 <tr>
                    <td style="text-align:left">NDA:</td>
                    <td style="text-align:left" colspan="6">
                        {nda or '   '}
                    </td>
                </tr>
                  <tr>
                    <td style="text-align:left">Comments:</td>
                    <td style="text-align:left" colspan="6">{po_approval_details.get('comment') or ''}</td>
                </tr>
           
        """

    if po_approval_details and po_approval_details.get("stock_detail"):
        stock_details_html = """
        <tr>
            <td colspan="7" style="text-align: center;">
                <h3 style="margin-bottom: 0px !important;">Stock Detail</h3>
            </td>
        </tr>
        <tr>
            <td style="text-align:left">Item Code</td>
            <td style="text-align:left">Item Name</td>
            <td style="text-align:left">Qty</td>
            <td style="text-align:left">Target Warehouse Qty</td>
            <td style="text-align:left">Current Stock</td>
            <td style="text-align:left">Demand</td>
            <td style="text-align:left">Additional</td>
        </tr>
        """

        for item in po_approval_details.get("stock_detail"):
            stock_details_html += f"""
            <tr>
                <td style="text-align:left">{item.get('item_code', '')}</td>
                <td style="text-align:left">{item.get('item_name', '')}</td>
                <td style="text-align:left">{frappe.format_value(item.get('qty', 0), {'fieldtype': 'Float'})}</td>
                <td style="text-align:left">{frappe.format_value(item.get('target_warehouse_qty', 0), {'fieldtype': 'Float'})}</td>
                <td style="text-align:left">{frappe.format_value(item.get('current_stock', 0), {'fieldtype': 'Float'})}</td>
                <td style="text-align:left">{frappe.format_value(item.get('demand', 0), {'fieldtype': 'Float'}) or 0}</td>
                <td style="text-align:left">{frappe.format_value(item.get('additional', 0), {'fieldtype': 'Float'}) or 0}</td>
            </tr>
            """

        po_approval_html += stock_details_html
    if po_approval_details and po_approval_details.get("price_comparison"):
        price_comparison_data = po_approval_details.get("price_comparison")[
            :6
        ]  # Limit to 6 entries

        price_comparison_html = """
        <tr>
            <td colspan="7" style="text-align: center;">
                <h3 style="margin-bottom: 0px !important;">Price Comparison</h3>
            </td>
        </tr>
        <tr>
            <td style="text-align:left"></td>
        """

        for i in range(len(price_comparison_data)):
            price_comparison_html += f"<td style='text-align:left'>L{i + 1}</td>"

        price_comparison_html += "</tr>"

        fields_dict = {
            "supplier_name": "Supplier Name",
            "quote_price_to_the_customer": "Quote Price to the Customer",
            "total_purchase_price": "Total Purchase Price",
            "supplier_quoted_price": "Supplier Quoted Price",
            "nagotiated": "Negotiated",
            "warranty_foc_spares": "Warranty / FOC Spares (%)",
            "lead_time": "Lead Time",
            "freight": "Freight",
            "rate_contract": "Rate Contract",
            "compliance__certificates_in_case_of_import": "Compliance / Certificates (In case of IMPORT)",
            "payment_terms": "Payment Terms",
            "incoterms_shipping_terms": "Incoterms/ Shipping Terms",
        }

        currency_fields = {
            "quote_price_to_the_customer",
            "total_purchase_price",
            "supplier_quoted_price",
            "nagotiated",
            "freight",
            "rate_contract",
        }

        for key, label in fields_dict.items():
            price_comparison_html += (
                f"<tr><td style='text-align:left'><b>{label}</b></td>"
            )

            for row in price_comparison_data:
                value = row.get(key, "") or ""

                if key in currency_fields and value:
                    value = frappe.format_value(value, {"fieldtype": "Currency"})

                if key == "compliance__certificates_in_case_of_import":
                    if value:
                        value = f"""
                        <button style="padding: 5px 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;" 
                        onclick="window.open('{value}', '_blank')">View Certificate</button>
                        """
                    else:
                        value = ""

                price_comparison_html += (
                    f'<td style="word-wrap: break-word; max-width: 200px;">{value}</td>'
                )

            price_comparison_html += "</tr>"

        po_approval_html += price_comparison_html
        po_approval_html += "</tbody></table>"
        return po_details_html + po_approval_html

    return po_details_html

@frappe.whitelist()
def fetch_document_details(doctype, docname):
    """
    API method to fetch document details via Frappe call.
    """
    details = get_document_details(doctype, docname)  
    return generate_html(details)