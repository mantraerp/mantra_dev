# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_column()
	data = get_data()
	return columns, data

def get_column():
	colunms = []
	colunms.append({"label": "Payment Entry Name", "fieldname": "name", "fieldtype": "Link", "options": "Payment Entry", "width": 200})
	colunms.append({"label": "Payment Type", "fieldname": "payment_type", "fieldtype": "Data","width": 75})
	colunms.append({"label": "Party", "fieldname": "party", "fieldtype": "Data","width": 100})
	colunms.append({"label": "Party Name", "fieldname": "party_name", "fieldtype": "Data","width": 150})
	colunms.append({"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data","width": 150})
	colunms.append({"label": "Narattion", "fieldname": "narration", "fieldtype": "Data", "width": 150})
	colunms.append({"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 150})
	colunms.append({"label": "Project", "fieldname": "project", "fieldtype": "Data", "width": 150})
	colunms.append({"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 150})
	colunms.append({"label": "Update Remarks", "fieldname": "update_remarks", "fieldtype": "Button", "width": 150})
	colunms.append({"label": "Get Details", "fieldname": "get_details", "fieldtype": "Button", "width": 150})
	return colunms

def get_data():
	data = f"""
		SELECT
			py.name as name,
			py.payment_type as payment_type,
			py.party as party,
			py.party_name as party_name,
			py.remarks as remarks,
			py.custom_type as type,
			py.docstatus,
			py.custom_project_type as project,
			py.paid_amount as paid_amount,
			(SELECT GROUP_CONCAT(
				CASE 
					WHEN per.reference_doctype = 'Purchase Invoice' 
						THEN CONCAT('Purchase Invoice (', per.reference_name, '): ', (SELECT pi.custom_narration FROM `tabPurchase Invoice` pi WHERE pi.name = per.reference_name))
					WHEN per.reference_doctype = 'Expense Claim' 
						THEN CONCAT('Expense Claim (', per.reference_name, '): ', (SELECT ec.remark FROM `tabExpense Claim` ec WHERE ec.name = per.reference_name))
					WHEN per.reference_doctype = 'Purchase Order' 
						THEN CONCAT('Purchase Order (', per.reference_name, '): ', (SELECT po.custom_purpose FROM `tabPurchase Order` po WHERE po.name = per.reference_name))
					WHEN per.reference_doctype = 'Sales Invoice' 
						THEN CONCAT('Sales Invoice (', per.reference_name, '): ', (SELECT si.remarks FROM `tabSales Invoice` si WHERE si.name = per.reference_name))
					WHEN per.reference_doctype = 'Sales Order' 
						THEN CONCAT('Sales Order (', per.reference_name, '): ', (SELECT so.custom_special_instructions_for_bill_and_dc FROM `tabSales Order` so WHERE so.name = per.reference_name))
					ELSE 
						NULL
				END SEPARATOR ',')
			FROM `tabPayment Entry Reference` per 
			WHERE per.parent = py.name) AS narration,
			CASE
				WHEN py.remarks IS NOT NULL AND py.remarks != '' THEN
					CONCAT(
							'<button class="btn btn-primary pt-0 pb-0 update_remarks" style="background-color: #28a745;color: white;"',
								'data-name="', py.name, '" ',
								'data-remarks="', IFNULL(py.remarks, ''), '"',
								'data-narration="', IFNULL((
									SELECT GROUP_CONCAT(
										CASE 
											WHEN per.reference_doctype = 'Purchase Invoice' 
												THEN CONCAT('Purchase Invoice (', per.reference_name, '): ', (SELECT pi.custom_narration FROM `tabPurchase Invoice` pi WHERE pi.name = per.reference_name))
											WHEN per.reference_doctype = 'Expense Claim' 
												THEN CONCAT('Expense Claim (', per.reference_name, '): ', (SELECT ec.remark FROM `tabExpense Claim` ec WHERE ec.name = per.reference_name))
											WHEN per.reference_doctype = 'Purchase Order' 
												THEN CONCAT('Purchase Order (', per.reference_name, '): ', (SELECT po.custom_purpose FROM `tabPurchase Order` po WHERE po.name = per.reference_name))
											WHEN per.reference_doctype = 'Sales Invoice' 
												THEN CONCAT('Sales Invoice (', per.reference_name, '): ', (SELECT si.remarks FROM `tabSales Invoice` si WHERE si.name = per.reference_name))
											WHEN per.reference_doctype = 'Sales Order' 
												THEN CONCAT('Sales Order (', per.reference_name, '): ', (SELECT so.custom_special_instructions_for_bill_and_dc FROM `tabSales Order` so WHERE so.name = per.reference_name))
											ELSE 
												NULL
										END SEPARATOR '<br>') 
									FROM `tabPayment Entry Reference` per 
									WHERE per.parent = py.name
								), ''), '" ',
								'data-type="', IFNULL(py.custom_type, ''), '" ',
								'data-project="', IFNULL(py.custom_project_type, ''), '" ',
							'>Update Remarks</button>'
						)
					ELSE
						NULL
				END AS update_remarks,
				CASE
					WHEN py.name IS NOT NULL AND py.name != '' THEN
						CONCAT(
							'<button class="btn btn-primary pt-0 pb-0 get_details" style="background-color: #007bff;color: white;" ',
								'data-name="', py.name, '" ',
							'>Get Details</button>'
						)
					ELSE NULL
            	END AS get_details
		FROM 
			`tabPayment Entry` as py
		WHERE
			py.docstatus = 1
	"""

	data = frappe.db.sql(data,as_dict=True)
	return data

@frappe.whitelist()
def update_remarks(payment_entry=None,remarks=None,type=None,project=None):
	#update remarks in Payment Entry 
	try:
		py_doc = frappe.get_doc("Payment Entry",payment_entry)
		if not py_doc:
			return {"status": "error", "message": "Payment Entry not found"}
		if remarks:
			frappe.db.set_value("Payment Entry", payment_entry, "remarks", remarks)
		if type:
			frappe.db.set_value("Payment Entry", payment_entry, "custom_type", type)
		if project:
			frappe.db.set_value("Payment Entry", payment_entry, "custom_project_type", project)
		frappe.db.commit()
		return {"status": "success", "message": "Payment Entry updated successfully"}
	except Exception as e:
		return {"status": "error", "message": str(e)}