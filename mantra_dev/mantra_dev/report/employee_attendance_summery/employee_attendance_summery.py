# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe
import re
import datetime
from frappe.utils import get_first_day, get_last_day


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Employee Code", "fieldname": "employee_code", "fieldtype": "Link", "options": "Employee", "width": 200},
		{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 300},
		{"label": "Present(days)", "fieldname": "present_days", "fieldtype": "Data", "width": 200},
		{"label": "Absent(days)", "fieldname": "absent_days", "fieldtype": "Data", "width": 200},
		{"label": "Taken Leave", "fieldname": "taken_leave", "fieldtype": "Data", "width": 200},
		{"label": "No.Of Holiday", "fieldname": "no_of_holiday", "fieldtype": "Data", "width": 200},
		{"label": "No.OF WeekOff", "fieldname": "no_of_weekoff", "fieldtype": "Data", "width": 200},
		{"label": "No.Of Paiddays", "fieldname": "no_of_paiddays", "fieldtype": "Data", "width": 200},
		{"label": "Total Days", "fieldname": "total_days", "fieldtype": "Data", "width": 200},
	]

def get_data(filters):
	from_date = get_first_day(f"{filters.year}-{filters.month}-01")
	to_date = get_last_day(from_date)

	conditions = f"at.attendance_date BETWEEN '{from_date}' AND '{to_date}'"
	
	if filters.employee_list:
		filters.employee = filters.employee + [value.strip() for value in re.split(r'[,\n]', filters['employee_list']) if value.strip()]

	if filters.employee:
		if len(filters.employee) == 1:
			conditions += f"AND at.employee = '{filters.employee[0]}'"
		else:
			conditions += f"AND at.employee IN {tuple(filters.employee)}"

	result = frappe.db.sql(f"""
		SELECT 
			at.employee AS employee_code,
			at.employee_name,
			COUNT(CASE WHEN at.custom_minop_status = 'P' THEN 1 END) AS present_days,
			COUNT(CASE WHEN at.custom_minop_status = 'A' THEN 1 END) AS absent_days,
			COUNT(CASE WHEN at.custom_minop_status = 'A' THEN 1 END) AS taken_leave,
			COUNT(CASE WHEN at.custom_minop_status = 'H' THEN 1 END) AS no_of_holiday,
			COUNT(CASE WHEN at.custom_minop_status = 'W' THEN 1 END) AS no_of_weekoff,
			COUNT(CASE WHEN at.custom_minop_status IN ('P', 'H', 'W') THEN 1 END) AS no_of_paiddays,
			COUNT(CASE WHEN at.custom_minop_status IN ('P', 'A', 'H', 'W') THEN 1 END) AS total_days
		FROM 
			`tabAttendance` AS at
		WHERE 
			{conditions}
		GROUP BY 
			at.employee, at.employee_name
	""", as_dict=True)

	
	return result


@frappe.whitelist(allow_guest=True)
def send_employee_attendace_summery_report_mail(filters):
	import json
	filters = json.loads(filters)

	default_attendance_status = {
		'P': 'Present(days)',
		'A': 'Absent(days)',
		'TL': 'Taken Leave',
		'H': 'No.Of Holiday',
		'W': 'No.OF WeekOff',
		'no_of_paiddays': 'No.Of Paiddays',
		'total_days': 'Total(days)'
	}

	attendance_status_count_list = {
		'no_of_paiddays': 0,
		'total_days': 0
	}
	employee_doc = frappe.db.get_value("Employee", filters.get('employee'), ["employee_name", "name"], as_dict=True)
	from_date = get_first_day(f"{filters.get('year')}-{filters.get('month')}-01")
	to_date = get_last_day(from_date)

	conditions = f"at.attendance_date BETWEEN '{from_date}' AND '{to_date}' AND at.employee = '{filters.get('employee')}'"
	query = f"""
		SELECT
			at.attendance_date,
			at.custom_minop_status as status,
			at.status as attendance_status
		FROM 
			`tabAttendance` AS at
		WHERE 
			{conditions}
	"""
	attendance_list = frappe.db.sql(query, as_dict=True)

	for at in attendance_list:
		if at.status not in attendance_status_count_list:
			attendance_status_count_list[at.status] = 0
		attendance_status_count_list[at.status] += 1
		if at.status in ['P', 'H', 'W']:
			attendance_status_count_list['no_of_paiddays'] += 1
		attendance_status_count_list['total_days'] += 1
	
	html = f"""
		<b>Employee Code:</b> {filters.get('employee')}<br>
		<b>Employee Name:</b> {employee_doc.get("employee_name")}
		<br>
		<h4>Attendance Summury:</h4>
		<table style="border: 1px solid black; border-collapse: collapse; width: 100%;">
			<thead>
				<tr style="text-align: center;">
	"""

	for key, value in default_attendance_status.items():
		html += f"""
			<th style="border: 1px solid black; padding: 4px;">{value}</th>
		"""
	
	html += f"""
				</tr>
			</thead>
			<tbody>
				<tr>
	"""

	for key, value in default_attendance_status.items():
		count = 0
		if key in attendance_status_count_list:
			count = attendance_status_count_list[key]
		html += f"""
			<td style="border: 1px solid black; padding: 4px;">{count}</td>
		"""
	
	html += """
				</tr>
			</tbody>
		</table>
		<br>
		<h4>Attendance List:</h4>
		<table style="border: 1px solid black; border-collapse: collapse; width: 100%;">
			<thead>
				<tr style="text-align: center;">
					<th style="border: 1px solid black; padding: 4px;">Date</th>
					<th style="border: 1px solid black; padding: 4px;">Status</th>
					<th style="border: 1px solid black; padding: 4px;">Minop Status</th>
				</tr>
			</thead>
			<tbody>
	"""

	for at in attendance_list:
		html += f"""
				<tr style="text-align: center;">
					<td style="border: 1px solid black; padding: 4px;">{frappe.utils.format_date(at.attendance_date)}</td>
					<td style="border: 1px solid black; padding: 4px;">{at.attendance_status}</td>
					<td style="border: 1px solid black; padding: 4px;">{at.status}</td>
				</tr>
		"""

	html += """
			</tbody>
		</table>
	"""

	month_abbr = datetime.date(2025, int(filters.get('month')), 1).strftime('%b')
	frappe.sendmail(recipients="meet.sherasiya@mantratec.com", subject=f"{month_abbr}-{filters.get('year')} - Attendance Summury Report", content=html, now=True)


	return html



# @frappe.whitelist(allow_guest=True)
# def create_attendance():
# 	data = [
# 		{
# 			"Emp_id": "HR-EMP-00008",
# 			"Date": "2025-02-01",
# 			"Status": "W",
# 			"half_day": "No",
# 			"leave_type": "",
# 			"leave": ""
# 		},
# 		{
# 			"Emp_id": "HR-EMP-00008",
# 			"Date": "2025-02-02",
# 			"Status": "W",
# 			"half_day": "No",
# 			"leave_type": "",
# 			"leave": ""
# 		},
# 		{
# 			"Emp_id": "HR-EMP-00008",
# 			"Date": "2025-02-03",
# 			"Status": "P",
# 			"half_day": "No",
# 			"leave_type": "",
# 			"leave": ""
# 		},
# 		{
# 			"Emp_id": "HR-EMP-00008",
# 			"Date": "2025-02-04",
# 			"Status": "A",
# 			"half_day": "No",
# 			"leave_type": "Paid",
# 			"leave": "TL"
# 		},
# 		{
# 			"Emp_id": "HR-EMP-00008",
# 			"Date": "2025-02-05",
# 			"Status": "A",
# 			"half_day": "No",
# 			"leave_type": "Paid",
# 			"leave": "TL"
# 		},
# 		{
# 			"Emp_id": "HR-EMP-00008",
# 			"Date": "2025-02-06",
# 			"Status": "A",
# 			"half_day": "No",
# 			"leave_type": "Paid",
# 			"leave": "TL"
# 		},
# 		{
# 			"Emp_id": "HR-EMP-00008",
# 			"Date": "2025-02-07",
# 			"Status": "A",
# 			"half_day": "No",
# 			"leave_type": "Paid",
# 			"leave": "TL"
# 		}
# 	]

# 	default_attendance_status = {
# 		'P': 'Present',
# 		'A': 'Absent',
# 		'W': 'Present',
# 		'H': 'Present'
# 	}

# 	frappe.set_user("Administrator")

# 	for d in data:
# 		doc = frappe.new_doc("Attendance")  # Create new Attendance document
# 		doc.update({
# 			"attendance_date": d.get("Date"), 
# 			"status": default_attendance_status.get(d.get("Status"), "Absent"),  # Use .get() to avoid KeyError
# 			"employee": d.get("Emp_id"), 
# 			"custom_minop_status": d.get("Status")
# 		})
# 		doc.insert(ignore_permissions=True)  # Insert the document
# 		doc.submit()
# 		frappe.db.commit()  # Ensure changes are committed
	
# 	return "Done"