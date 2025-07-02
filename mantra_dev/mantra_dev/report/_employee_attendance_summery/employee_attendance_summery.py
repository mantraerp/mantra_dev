# Copyright (c) 2025, Foram Shah and contributors
# For license information, please see license.txt

import frappe
import re
import datetime
from frappe.utils import get_first_day, get_last_day, date_diff,getdate # type: ignore


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
        # {"label": "Joining Date", "fieldname": "date_of_joining", "fieldtype": "Date", "width": 200},
        # {"label": "Dyas Diff(From 1st Day Of Month to Joining Date)", "fieldname": "days_difference", "fieldtype": "Data", "width": 200},
        # {"label": "Relieving Date", "fieldname": "relieving_date", "fieldtype": "Date", "width": 200},
        # {"label": "Dyas Diff(From Last Day to Reliving Day)", "fieldname": "rel_days_difference", "fieldtype": "Data", "width": 200},
    ]

def get_data(filters):
    from_date = get_first_day(f"{filters.year}-{filters.month}-01")
    to_date = get_last_day(from_date)

    conditions = f"at.docstatus =1 AND at.attendance_date BETWEEN '{from_date}' AND '{to_date}'"

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
            DATE(emp.date_of_joining) AS date_of_joining,
            DATEDIFF(emp.date_of_joining, DATE_FORMAT(emp.date_of_joining, '%Y-%m-01')) AS days_difference,
            DATE(emp.relieving_date) AS relieving_date,
            ABS(DATEDIFF(emp.relieving_date, '{to_date}')) AS rel_days_difference,
            SUM(
                CASE
                    WHEN at.custom_minop_status IN ("P","PW","PH","W","WH","H","HW") AND at.status = 'Half Day' THEN 0.5
                    WHEN at.custom_minop_status IN ("P","PW","PH","W","WH","H","HW") AND at.status = 'On Leave' THEN 0
                    WHEN at.custom_minop_status IN ('P', 'PW', 'PH', 'WH', 'HW') THEN 1
                    WHEN at.custom_minop_status IN ('HD') THEN 0.5
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') AND at.leave_type NOT IN ('Leave Without Pay', '') AND at.status = 'Half Day' THEN 0.5
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') AND at.leave_type NOT IN ('Leave Without Pay', '') AND at.status = 'Present' THEN 1
                    ELSE 0
                END
            ) AS present_days,
            SUM(
                CASE 
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') AND at.leave_type NOT IN ('Leave Without Pay', '') AND at.status = 'Present' THEN 0
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') AND at.leave_type NOT IN ('Leave Without Pay', '') AND at.status = 'Half Day' THEN 0.5
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') THEN 1
                    WHEN at.custom_minop_status IN ("P","PW","PH","W","WH","H","HW") AND at.status = 'Half Day' AND at.leave_type = 'Leave Without Pay' THEN 0.5
                    WHEN at.custom_minop_status IN ("P","PW","PH","W","WH","H","HW") AND at.status = 'On Leave' AND at.leave_type = 'Leave Without Pay' THEN 1
                    WHEN at.custom_minop_status = 'HD' AND at.leave_type = 'Leave Without Pay' THEN 0.5
                    ELSE 0
                END
            ) AS absent_days,
            SUM(
                CASE
                    WHEN at.custom_minop_status IN ('TL', 'CL', 'SL', 'WL', 'ML', 'BL', 'BR', 'LL', 'CO', 'EL', 'OD', 'LC') THEN 1
                    WHEN at.custom_minop_status = 'HD' AND at.leave_type != 'Leave Without Pay' THEN 0.5
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') AND at.leave_type NOT IN ('Leave Without Pay', '') AND at.status = 'Half Day' THEN 0.5
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') AND at.leave_type NOT IN ('Leave Without Pay', '') AND at.status = 'Present' THEN 1
                    WHEN at.custom_minop_status IN ("P","PW","PH","WH","HW") AND at.status = 'Half Day' AND at.leave_type NOT IN ('Leave Without Pay', '') THEN 0.5
                    WHEN at.custom_minop_status IN ("P","PW","PH","WH","HW") AND at.status = 'On Leave' AND at.leave_type NOT IN ('Leave Without Pay', '') THEN 1
                    ELSE 0
                END
            ) AS taken_leave,
            SUM(CASE WHEN at.custom_minop_status = 'H' THEN 1 ELSE 0 END) AS no_of_holiday,
            SUM(CASE WHEN at.custom_minop_status = 'W' THEN 1 ELSE 0 END) AS no_of_weekoff,
            SUM(
                CASE 
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') AND at.leave_type NOT IN ('Leave Without Pay', '') AND at.status = 'Half Day' THEN 0.5
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') AND at.leave_type NOT IN ('Leave Without Pay', '') AND at.status = 'Present' THEN 1
                    WHEN at.custom_minop_status IN ('A', 'XX', 'LH', 'E') THEN 0
                    WHEN at.custom_minop_status IN ("P","PW","PH","WH","HW") AND at.status = 'Half Day' AND at.leave_type = 'Leave Without Pay' THEN 0.5
                    WHEN at.custom_minop_status IN ("P","PW","PH","WH","HW") AND at.status = 'On Leave' AND at.leave_type = 'Leave Without Pay' THEN 0
                    WHEN at.custom_minop_status = 'HD' AND at.leave_type = 'Leave Without Pay' THEN 0.5
                    WHEN at.status = 'On Leave' AND at.leave_type = 'Leave Without Pay' THEN 0
                    ELSE 1
                END
            ) AS no_of_paiddays,
            {date_diff(to_date, from_date) + 1} AS total_days
        FROM 
            `tabAttendance` AS at
        LEFT JOIN
            `tabEmployee` AS emp ON at.employee = emp.name
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
        'total_days': 'Total(days)',
        'difference': 'Days Difference (From 1st Day Of Month to Joining Date)',
        "relieving_difference": 'Relieving Diff. (From Relieving Date to Last Day Of Month)'
    }

    attendance_status_count_list = {
        'P': 0,
        'A': 0,
        'TL': 0,
        'W': 0,
        'H': 0,
        'no_of_paiddays': 0,
        'total_days': date_diff(filters.get('to_date'), filters.get('from_date')) + 1,
        'difference': 0,
        'relieving_difference': 0
    }
    employee_doc = frappe.db.get_value("Employee", filters.get('employee'), ["employee_name", "prefered_email","date_of_joining","relieving_date"], as_dict=True)

    if not employee_doc.get("employee_name"):
        return "Employee Name is not found"

    if not employee_doc.get("prefered_email"):
        return "Prefered Email is not set in Employee"

    if not employee_doc.get("date_of_joining"):
        return "Date Of Joining is not set in Employee"
    

    joining_date = getdate(employee_doc.get('date_of_joining'))
    first_day = joining_date.replace(day=1)
    days_difference = (joining_date - first_day).days

    attendance_status_count_list['difference'] = days_difference

    rel_date = None
    if employee_doc.get("relieving_date"):
        rel_date = getdate(employee_doc.get("relieving_date"))
        last_day = get_last_day(rel_date)
        rel_days_difference = abs((last_day - rel_date).days)
        attendance_status_count_list['relieving_difference'] = rel_days_difference

    conditions = f"at.docstatus = 1 AND at.attendance_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}' AND at.employee = '{filters.get('employee')}'"
    query = f"""
        SELECT
            at.attendance_date,
            at.custom_minop_status as status,
            at.leave_type,
            at.status as attendance_status
        FROM 
            `tabAttendance` AS at
        WHERE 
            {conditions}
        ORDER BY
            at.attendance_date
    """
    
    attendance_list = frappe.db.sql(query, as_dict=True)

    if attendance_list:
        for at in attendance_list:
            # if at.status not in attendance_status_count_list:
            #     attendance_status_count_list[at.status] = 0

            if (at.status == 'HD' and at.leave_type != 'Leave Without Pay'):
                attendance_status_count_list['P'] += 0.5
                attendance_status_count_list['TL'] += 0.5
            elif (at.status in ['PW', 'PH', 'WH', 'HW']):
                attendance_status_count_list['P'] += 1
            elif (at.status == 'HD' and at.leave_type == 'Leave Without Pay'):
                attendance_status_count_list['P'] += 0.5
                attendance_status_count_list['A'] += 0.5
            elif (at.status in ('A', 'XX', 'LH', 'E') and at.leave_type in ('HTL','HCL','HSL','HWL','HML','HML','HBL','HBR','HLL','HCO','HEL','HOD')):
                attendance_status_count_list['P'] += 0.5
                attendance_status_count_list['A'] += 0.5
            elif (at.status in ('A', 'XX', 'LH', 'E') and at.leave_type in ("TL", "CL", "SL", "WL", "ML", "BL", "BR", "LL", "CO", "EL", "OD",'LC' )):
                attendance_status_count_list['P'] += 1
            # elif (at.status == 'XX'):
            #     attendance_status_count_list['A'] += 1
            # elif (at.status in ['LH', 'E']):
            #     attendance_status_count_list['A'] += 0.5
            #     attendance_status_count_list['P'] += 0.5
            elif (at.status in ('TL', 'CL', 'SL', 'WL', 'ML', 'BL', 'BR', 'LL', 'CO', 'EL', 'OD', 'LC')):
                attendance_status_count_list['TL'] += 1

            if at.status in ['P', 'A', 'H', 'W']:
                attendance_status_count_list[at.status] += 1

            if at.status in ('A', 'XX') and at.leave_type == 'Leave Without Pay':
                continue
            elif at.attendance_status == 'On Leave' and at.leave_type == 'Leave Without Pay':
                continue
            elif at.status == 'HD' and at.leave_type == 'Leave Without Pay':
                attendance_status_count_list['no_of_paiddays'] += 0.5
            elif at.status in ['A', 'XX', 'LH', 'E'] and at.leave_type in ('HTL','HCL','HSL','HWL','HML','HML','HBL','HBR','HLL','HCO','HEL','HOD'):
                attendance_status_count_list['no_of_paiddays'] += 0.5
            elif at.status in ['A', 'XX', 'LH', 'E'] and at.leave_type in ("TL", "CL", "SL", "WL", "ML", "BL", "BR", "LL", "CO", "EL", "OD",'LC' ):
                attendance_status_count_list['no_of_paiddays'] += 1
            else:
                attendance_status_count_list['no_of_paiddays'] += 1

        html = f"""
            <b>Employee Code:</b> {filters.get('employee')}<br>
            <b>Employee Name:</b> {employee_doc.get("employee_name")}<br>
            <b>Date Of Joining:</b> {frappe.utils.format_date(joining_date) if joining_date else ''}<br>
            <b>Relieving Date:</b> {frappe.utils.format_date(rel_date) if rel_date else ''}<br>
            <b>Date Range:</b> {frappe.utils.format_date(filters.get("from_date"))} to {frappe.utils.format_date(filters.get("to_date"))}
            <br>
            <h4>Attendance Summury:</h4>
            <table style="border: 1px solid black; border-collapse: collapse; width: 100%;">
                <thead>
                    <tr style="text-align: center;">
        """
        frappe.log_error("attendance", str(attendance_status_count_list))

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
                        <th style="border: 1px solid black; padding: 4px;">Leave Type</th>
                    </tr>
                </thead>
                <tbody>
        """

        for at in attendance_list:
            html += f"""
                    <tr style="text-align: center;">
                        <td style="border: 1px solid black; padding: 4px;">{frappe.utils.format_date(at.attendance_date)}</td>
                        <td style="border: 1px solid black; padding: 4px;" class="{(at.attendance_status).replace(" ", "-")}">{at.attendance_status}</td>
                        <td style="border: 1px solid black; padding: 4px;">{at.status}</td>
                        <td style="border: 1px solid black; padding: 4px;">{at.leave_type or ''}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        """

        frappe.sendmail(recipients=employee_doc.get("prefered_email"), subject=f"{frappe.utils.format_date(filters.get('from_date'))} to {frappe.utils.format_date(filters.get('to_date'))} - Attendance Summury Report", content=html)


        return "Attendance Summury Send in Employee Mail"

    else:
        return f"No attendance records found for the employee within the date range {filters.get('from_date')} to {filters.get('to_date')}"