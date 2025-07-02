# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe
import json
from mantra_dev.backend_code.globle import create_notification_log

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": "Material Request", "fieldname": "material_request", "fieldtype": "Link", "options": "Material Request", "width": 250},
		{"label": "Material Request Type", "fieldname": "material_request_type", "fieldtype": "Data", "width": 200},
		{"label": "Material Request Status", "fieldname": "material_request_status", "fieldtype": "Data", "width": 200},
		{"label": "Transaction Date", "fieldname": "transaction_date", "fieldtype": "Date", "width": 200},
		{"label": "Required By Date", "fieldname": "required_by_date", "fieldtype": "Date", "width": 200},
		{"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 250},
		{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 250},
		{"label": "Requested Qty", "fieldname": "requested_qty", "fieldtype": "Float", "width": 150},
		{"label": "Ordered Qty", "fieldname": "ordered_qty", "fieldtype": "Float", "width": 150},
		{"label": "Received Qty", "fieldname": "received_qty", "fieldtype": "Float", "width": 150},
		{"label": "Pending Transferred Qty", "fieldname": "pending_transferred_qty", "fieldtype": "Float", "width": 200},
		{"label": "Transferred Qty", "fieldname": "transferred_qty", "fieldtype": "Float", "width": 150},
		{"label": "Material Transfer", "fieldname": "material_transfer", "fieldtype": "Data", "width": 200},
		{"label": "Received Material", "fieldname": "received_material", "fieldtype": "Data", "width": 200},
	]


def create_button(label: str, style: str, class_id: str, data_attr: dict) -> str:
    """
    Create an HTML button with specified attributes.
    """
    data_string = " ".join([f"data-{key}='{value}'" for key, value in data_attr.items()])
    return f"<button class='btn btn-primary pt-0 pb-0 {class_id}' style='{style}' {data_string}>{label}</button>"


def fetch_material_requests(filters: dict) -> list:
    """
    Fetch material requests based on the provided filters.

    Returns:
        list: List of material request names.
    """
    mr_filters = {
        "material_request_type": ["in", ["Purchase", "Material Transfer"]] if not filters.get("material_request_type") else filters["material_request_type"],
        "docstatus": ["!=", 2],
        "transaction_date": ["between", [filters.get("from_date"), filters.get("to_date")]],
    }

    if filters.get("material_request_id"):
        mr_filters["name"] = ["in", filters["material_request_id"]]

    if filters.get("material_request_status"):
        mr_filters["status"] = filters["material_request_status"]

    return frappe.db.get_list(
        "Material Request",
        filters=mr_filters,
        pluck="name",
        order_by="creation desc",
    )


def process_items(doc, row_dict: dict) -> tuple:
    """
    Process items in a material request document and update the row dictionary.

    Returns:
        tuple: (list of item rows, flag for material transfer button).
    """
    material_request_items_row = []
    transfer_flag = 0

    for item in doc.items:
        item_row = {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "requested_qty": item.qty,
            "indent": 1
        }

        if doc.material_request_type == "Purchase":
            item_row.update({
                "ordered_qty": item.ordered_qty,
                "received_qty": item.received_qty,
            })
            if (item.received_qty - item.custom_material_transfer_qty) > 0:
                transfer_flag = 1

            row_dict["ordered_qty"] += item.ordered_qty
            row_dict["received_qty"] += item.received_qty

        elif doc.material_request_type == "Material Transfer":
            draft_stock_entry = frappe.db.get_all(
                "Stock Entry Detail", 
                {"material_request_item": item.name, "docstatus": 0}, 
                ["parent", "qty"]
            )

            if draft_stock_entry:
                stock_qty = sum(entry.qty for entry in draft_stock_entry)
                stock_entry_parents = [entry.parent for entry in draft_stock_entry]
                item_row["pending_transferred_qty"] = stock_qty
                row_dict["received_material"] = create_button(
                    "Received Material",
                    "background-color: cadetblue",
					"received_material",
                    {"material_request": ",".join(stock_entry_parents)}
                )
                row_dict["pending_transferred_qty"] += stock_qty

            item_row["transferred_qty"] = item.ordered_qty
            row_dict["transferred_qty"] += item.ordered_qty

        material_request_items_row.append(item_row)
        row_dict["requested_qty"] += item.qty

    return material_request_items_row, transfer_flag


def get_data(filters):
    """
    Fetch material request data based on filters.
    """
    data = []
    material_request_list = fetch_material_requests(filters)

    for material_request in material_request_list:
        doc = frappe.get_doc("Material Request", material_request)
        row_dict = frappe._dict({
            "material_request": doc.name,
            "material_request_type": doc.material_request_type,
            "material_request_status": doc.status,
            "transaction_date": doc.transaction_date,
            "required_by_date": doc.schedule_date,
            "requested_qty": 0,
            "ordered_qty": 0,
            "received_qty": 0,
            "transferred_qty": 0,
            "pending_transferred_qty": 0,
            "indent": 0
        })

        material_request_items_row, transfer_flag = process_items(doc, row_dict)

        if transfer_flag == 1:
            row_dict["material_transfer"] = create_button(
                "Material Transfer",
                "background-color: grey",
				"create_material_transfer",
                {"material_request": doc.name}
            )

        data.append(row_dict)
        data.extend(material_request_items_row)

    return data


@frappe.whitelist()
def make_material_transfer_material_request(docname, items, source_warehouse, target_warehouse, stock_entry_type_reference):
	"""
		Creates a new Material Request of type "Material Transfer" for specified items and quantities. 
		Updates the `custom_material_transfer_qty` in the original Material Request and appends the corresponding 
		items to the new request. Saves and submits the new Material Request and notifies warehouse managers 
		of the target warehouse about the created transfer request.
	"""
	try:
		items = json.loads(items)
		material_request_doc = frappe.get_doc("Material Request", docname)
		new_doc = frappe.get_doc({
			"doctype": "Material Request",
			"material_request_type": "Material Transfer",
			"transaction_date": frappe.utils.nowdate(),
			"schedule_date": frappe.utils.nowdate(),
			"custom_stock_entry_type_reference": stock_entry_type_reference,
			"set_from_warehouse": source_warehouse,
			"set_warehouse": target_warehouse,
			"custom_approval_from_warehouse_manager": 1
		})
		for item in material_request_doc.items:
			duplicate_item = item
			for it in items:
				if ((it.get('item_code') == item.item_code) and (it.get('transfer_qty') > 0)):
					frappe.db.set_value("Material Request Item", item.name, "custom_material_transfer_qty", item.custom_material_transfer_qty + it.get('transfer_qty'))
					duplicate_item.schedule_date = frappe.utils.nowdate()
					duplicate_item.warehouse = target_warehouse
					duplicate_item.from_warehouse = source_warehouse
					duplicate_item.ordered_qty = ""
					duplicate_item.qty = it.get('transfer_qty')
					duplicate_item.received_qty = ""
					duplicate_item.custom_material_transfer_qty = ""
					new_doc.append("items", duplicate_item)

		new_doc.save()
		# new_doc.submit()
		frappe.db.commit()

		return {
			"status": "success",
			"message": f"""Material Transfer Request <a href="{frappe.utils.get_url_to_form('Material Request', new_doc.name)}" target="_blank">{new_doc.name}</a> has been created successfully. Please review it."""
		}
	except Exception as e:
		# Rollback changes in case of failure
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Material Transfer Request Creation Error")
		return {
			"status": "error",
			"message": f"An error occurred while creating the Material Transfer Request: {str(e)}"
		}


@frappe.whitelist()
def get_material_transfer_items(docname):
	"""
		Fetching how much material request item is pending for transfer
	"""
	items = []
	material_request_doc = frappe.get_doc("Material Request", docname)
	for item in material_request_doc.items:
		items.append({
			'item_code': item.item_code,
			'item_name': item.item_name,
			'transfer_qty': item.received_qty - item.custom_material_transfer_qty,
		})
	return items


@frappe.whitelist()
def submit_material_request_stock_entry(docname_list):
	"""
		It verifies the material is received, then submits the stock entry of the material transfer 
		and sends a notification to the particular user who created it
		and sends a notification to the current user employee report_to and department_hod.
	"""
	try:
		docname_list = json.loads(docname_list)
		department_hod, emloyee_reprot_to_user_id = None, None

		# Fetch the current user employee report_to and their department_hod_user
		employee_report_to, employee_department = frappe.db.get_value("Employee", {'user_id': frappe.session.user}, ["reports_to", "department"]) or [None, None]
		if employee_department:
			department_hod = frappe.db.get_value("Department", employee_department, "custom_department_head")
		if employee_report_to:
			emloyee_reprot_to_user_id = frappe.db.get_value("Employee", employee_report_to, "user_id")

		for stock_id in docname_list:
			stock_entry_doc = frappe.get_doc("Stock Entry", stock_id)
			stock_entry_doc.submit()

			# Fetch stock entry source warehouse manager list and send notification to them
			warehouse_manager_list = frappe.db.get_all("Warehouse Manager", {'parent': stock_entry_doc.items[0].s_warehouse}, pluck="warehouse_manager")
			for user in warehouse_manager_list:
				create_notification_log(
					subject= f"Material Requeest {stock_entry_doc.custom_material_request_no} Material Transfer Completed",
					content= f"Material Requeest {stock_entry_doc.custom_material_request_no} Material Transfer Completed",
					document_type= "Material Request",
					document_name= stock_entry_doc.custom_material_request_no,
					for_user= user
				)
			if warehouse_manager_list:
				# Send Email to the Warehouse Manager When Material Are Recevied by Employee
				subject, content = submit_material_request_mail_content_for_warehouse_manager(doc_name = stock_entry_doc.custom_material_request_no, items = stock_entry_doc.items)
				frappe.sendmail(recipients=warehouse_manager_list, subject=subject, content=content, now=True)

			# Send the Notification and Email to the department hod
			if department_hod:
				create_notification_log(
					subject= f"Material Requeest {stock_entry_doc.custom_material_request_no} Requested Material Received",
					content= f"Material Requeest {stock_entry_doc.custom_material_request_no} Requested Material Received",
					document_type= "Material Request",
					document_name= stock_entry_doc.custom_material_request_no,
					for_user= department_hod
				)
				subject, content = submit_material_request_mail_content_for_emp_or_hod(doc_name = stock_entry_doc.custom_material_request_no, items = stock_entry_doc.items)
				frappe.sendmail(recipients=department_hod, subject=subject, content=content, now=True)

			# Send the Notification and Email to the employee reporting person
			if emloyee_reprot_to_user_id:
				create_notification_log(
					subject= f"Material Requeest {stock_entry_doc.custom_material_request_no} Requested Material Received",
					content= f"Material Requeest {stock_entry_doc.custom_material_request_no} Requested Material Received",
					document_type= "Material Request",
					document_name= stock_entry_doc.custom_material_request_no,
					for_user= emloyee_reprot_to_user_id
				)
				subject, content = submit_material_request_mail_content_for_emp_or_hod(doc_name = stock_entry_doc.custom_material_request_no, items = stock_entry_doc.items)
				frappe.sendmail(recipients=emloyee_reprot_to_user_id, subject=subject, content=content, now=True)

		return {
			"status": "success",
			"message": f"""Stock Entry has been successfully submitted. Please click here to view: <a href="{frappe.utils.get_url_to_form('Stock Entry', docname_list[0])}" target="_blank">{docname_list[0]}</a>"""
		}
	except Exception as e:
		# Log and return the error
		frappe.log_error(frappe.get_traceback(), "Stock Entry Submission Error")
		return {
			"status": "error",
			"message": f"An error occurred while submitting the Stock Entry: {str(e)}"
		}


def generate_email_table(items):
    rows = "".join(
        f"""
        <tr>
            <td style="border: 1px solid black; padding: 4px;">{item.idx}</td>
            <td style="border: 1px solid black; padding: 4px;">{item.item_code}</td>
            <td style="border: 1px solid black; padding: 4px;">{item.item_name}</td>
            <td style="border: 1px solid black; padding: 4px;">{item.qty} {item.uom}</td>
        </tr>
        """
        for item in items
    )
    return rows

def submit_material_request_mail_content_for_warehouse_manager(doc_name, items):
	# This Function is Send the Email to the Warehouse Manager When Material are received by employee
	# Subject for the email
	subject = f"Material Request {doc_name} Material Transfer Completed"

	# Base content structure
	content = f"""
		Dear User,
		<br><br>
		Greetings of the day!
		<br><br>
		Items issued against the Material Transfer Request, {doc_name} has been received by the {frappe.session.user}.
		<br><br>
		<table style="border: 1px solid black; border-collapse: collapse; width: 100%;">
			<thead>
				<tr style="text-align: center;">
					<th style="border: 1px solid black; padding: 4px;">S No.</th>
					<th style="border: 1px solid black; padding: 4px;">Item Code</th>
					<th style="border: 1px solid black; padding: 4px;">Item Name</th>
					<th style="border: 1px solid black; padding: 4px;">Qty</th>
				</tr>
			</thead>
			<tbody>
	"""

	content += generate_email_table(items)

	# Append the footer and action buttons
	content += f"""
			</tbody>
		</table>
		<br><br>
		Take action by approving or rejecting the request on the ERP Portal:
		<br>
		<a href="{frappe.utils.get_url_to_form('Material Request', doc_name)}" target="_blank"
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Material Request</a>
		<br><br>
		In case of any query, please raise a ticket using this form:
		<br>
		<a href="https://mantratec.milaap.ai/matratec.helpdesk/new" target="_blank" 
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Support Form</a>
		<br><br><br>
		Thank You
		<br>
		ERP Team
	"""

	return subject, content


def submit_material_request_mail_content_for_emp_or_hod(doc_name, items):
	# This Function is Send the Email to the department of hod and employee reporting person When Material are received by employee

	# Subject for the email
	subject = f"Material Request {doc_name} Requested Material Received "

	# Base content structure
	content = f"""
		Dear User,
		<br><br>
		Greetings of the day!
		<br><br>
		Employee {frappe.session.user} has received the items as per his/her request raised.
		<br><br>
		<table style="border: 1px solid black; border-collapse: collapse; width: 100%;">
			<thead>
				<tr style="text-align: center;">
					<th style="border: 1px solid black; padding: 4px;">S No.</th>
					<th style="border: 1px solid black; padding: 4px;">Item Code</th>
					<th style="border: 1px solid black; padding: 4px;">Item Name</th>
					<th style="border: 1px solid black; padding: 4px;">Qty</th>
				</tr>
			</thead>
			<tbody>
	"""

	content +=  generate_email_table(items)

	# Append the footer and action buttons
	content += f"""
			</tbody>
		</table>
		<br><br>
		Take action by approving or rejecting the request on the ERP Portal:
		<br>
		<a href="{frappe.utils.get_url_to_form('Material Request', doc_name)}" target="_blank"
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Material Request</a>
		<br><br>
		In case of any query, please raise a ticket using this form:
		<br>
		<a href="https://mantratec.milaap.ai/matratec.helpdesk/new" target="_blank" 
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Support Form</a>
		<br><br><br>
		Thank You
		<br>
		ERP Team
	"""

	return subject, content


def send_material_request_submit_mail_content(self):
	# Send Email When the Sumbit the Material Transfer Material Request by Warehouse Manager
	# Subject for the email
	subject = f"Requested Material Dispatched"

	# Base content structure
	content = f"""
		Dear User,
		<br><br>
		Greetings of the day!
		<br><br>
		Your request for material transfer has been approved and processed by the warehouse manager.
		<br> 
		Please confirm the arrival of the requested items mentioned below by clicking on "Received" Button in 
		the "Material Request Tracking Report" once you receives the items. 
		<br><br>
		<table style="border: 1px solid black; border-collapse: collapse; width: 100%;">
			<thead>
				<tr style="text-align: center;">
					<th style="border: 1px solid black; padding: 4px;">S No.</th>
					<th style="border: 1px solid black; padding: 4px;">Item Code</th>
					<th style="border: 1px solid black; padding: 4px;">Item Name</th>
					<th style="border: 1px solid black; padding: 4px;">Qty</th>
				</tr>
			</thead>
			<tbody>
	"""

	content += generate_email_table(self.items)

	# Append the footer and action buttons
	content += f"""
			</tbody>
		</table>
		<br><br>
		Here is your Material Request Tracking Report:
		<br>
		<a href="{frappe.utils.get_url()}/app/query-report/Material%20Request%20Tracking?material_request_id={self.name}" target="_blank"
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Material Request Tracking Report</a>
		<br><br>
		In case of any query, please raise a ticket using this form:
		<br>
		<a href="https://mantratec.milaap.ai/matratec.helpdesk/new" target="_blank" 
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Support Form</a>
		<br><br><br>
		Thank You
		<br>
		ERP Team
	"""

	return subject, content


def create_material_request_mail_content(self):
	# Send Email to Warehouse Manager When the Material Request is Created by Employee For Material Transfer

	# Subject for the email
	subject = f"Approval Request for {self.name} Material Transfer to Employee"

	# Base content structure
	content = f"""
		Dear User,
		<br><br>
		Greetings of the day!
		<br><br>
		{frappe.session.user} has raised a material transfer request for:
		<br><br>
		<table style="border: 1px solid black; border-collapse: collapse; width: 100%;">
			<thead>
				<tr style="text-align: center;">
					<th style="border: 1px solid black; padding: 4px;">S No.</th>
					<th style="border: 1px solid black; padding: 4px;">Item Code</th>
					<th style="border: 1px solid black; padding: 4px;">Item Name</th>
					<th style="border: 1px solid black; padding: 4px;">Qty</th>
				</tr>
			</thead>
			<tbody>
	"""

	content += generate_email_table(self.items)

	# Append the footer and action buttons
	content += f"""
			</tbody>
		</table>
		<br><br>
		Take action by approving or rejecting the request on the ERP Portal:
		<br>
		<a href="{frappe.utils.get_url_to_form('Material Request', self.name)}" target="_blank"
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Material Request</a>
		<br><br>
		In case of any query, please raise a ticket using this form:
		<br>
		<a href="https://mantratec.milaap.ai/matratec.helpdesk/new" target="_blank" 
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Support Form</a>
		<br><br><br>
		Thank You
		<br>
		ERP Team
	"""

	return subject, content

@frappe.whitelist()
def reject_material_request_mail_content(docname, transfer_type, doc_owner):
	# Send Email to Owner When the Material Request is Rejected

	# Subject for the email
	subject = f"Material Request {docname} is Rejected"

	# Base content structure
	content = f"""
		Dear User,
		<br><br>
		Greetings of the day!
		<br><br>
		Your request for {transfer_type.lower()} has been rejected by the warehouse manager.
		<br><br>
		Please contact the HOD or Warehouse Manager to resolve the case.
		<br>
		<a href="{frappe.utils.get_url_to_form('Material Request', docname)}" target="_blank"
			style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
			color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
			border: 1px solid #007bff; text-align: center; margin-top: 8px;">
			Open Material Request
		</a>
		<br><br>
		Take action by approving or rejecting the request on the ERP Portal:
		<br>
		<a href="{frappe.utils.get_url_to_form('Material Request', docname)}" target="_blank"
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Material Request</a>
		<br><br>
		In case of any query, please raise a ticket using this form:
		<br>
		<a href="https://mantratec.milaap.ai/matratec.helpdesk/new" target="_blank" 
		style="display: inline-block; padding: 6px 10px; font-size: 12px; font-weight: bold; 
		color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 8px; 
		border: 1px solid #007bff; text-align: center; margin-top: 8px;">Open Support Form</a>
		<br><br><br>
		Thank You
		<br>
		ERP Team
	"""

	frappe.sendmail(recipients=doc_owner, subject=subject, content=content, now=True)
	create_notification_log(
		subject= f"Material Request {docname} is Rejected",
		content= f"Material Request {docname} is Rejected",
		document_type= "Material Request",
		document_name= docname,
		for_user= doc_owner
	)