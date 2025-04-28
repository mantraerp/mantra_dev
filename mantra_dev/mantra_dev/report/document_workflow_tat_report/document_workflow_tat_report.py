# Copyright (c) 2024, Software At Work (India) Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import format_datetime, time_diff_in_seconds, getdate, format_duration


def execute(filters=None):
    columns, data = get_data_and_column(filters)
    return columns, data


def get_data_and_column(filters):
    #fetch excempted transition
    exempted = []
    workflow = frappe.get_doc("Workflow",{'document_type':filters.doctype,'is_active':1})
    for transition in workflow.transitions:
        if transition.custom_exempted == 1:
            exempted.append({'state':transition.state,'next_state':transition.next_state})

    workflow_status_list = tuple(set(i.state for i in workflow.states))
    
    columns = [
        {
            "label": _("DocType"),
            "fieldname": "doctype",
            "fieldtype": "Link",
            "options": "DocType",
            "width": 200,
        },
        {
            "label": _("Document Name"),
            "fieldname": "docname",
            "fieldtype": "Link",
            "options": filters.doctype,
            "width": 350,
        },
        {
            "label": _("Draft Creation Time"),
            "fieldname": "draft",
            "fieldtype": "Datetime",
            "width": 150,
        },
    ]


    for wo in workflow_status_list:
        columns.append({
            "label": _(f"{wo}"),
            "fieldname": wo.lower().replace(" ", "_"),
            "fieldtype": "Duration",
            "width": 150,
        })

    columns += [{
        "label": _("Default Time"),
        "fieldname": "default_time",
        "fieldtype": "Duration",
        "width": 120,
    },{
        "label": _("Time Taken"),
        "fieldname": "diff",
        "fieldtype": "Duration",
        "width": 120,
    },
    {
        "label": _("Time Variance"),
        "fieldname": "time_variance",
        "fieldtype": "Duration",
        "width": 120,
    }]

    list_filters = {
        'docstatus': ['<', 2]
    }
    if filters.from_date and filters.to_date:
       list_filters["creation"] = ["between", [filters.from_date, filters.to_date]]

    if filters.docname:
        list_filters["name"] = ["=", filters.docname]

    doc_list = frappe.db.get_list(
        filters.doctype,
        filters=list_filters,
        order_by="creation ASC",
        fields=["name", "creation", "owner"],
    )

    data = []

    for name in doc_list:
        row_data = {
            "doctype": filters.doctype,
            "docname": name.name,
            "draft": name.creation,
            "user": name.owner,
            "default_time": 0,
            "time_variance": 0,
            "diff": 0,
        }

        row_list = frappe.db.sql(
            """SELECT
            name,
            reference_doctype,
            reference_name,
            content,
            creation,
            owner
            FROM
                `tabComment`
            WHERE
                reference_doctype = %(doctype)s
                AND reference_name = %(docname)s
                AND comment_type = "Workflow"
            ORDER BY
                creation ASC;""",
            {"doctype": filters.doctype, "docname": name.name},
            as_dict=1,
        )
        previous_state = workflow.states[0].state
        submition_date = name.creation

        for row in row_list:
            default_time = frappe.db.get_value('Workflow Transition',{'parent':workflow.name,"state":previous_state,"next_state":row.content},"custom_default_time")
            if not default_time:
                default_time = 0

            if not check_exempted(previous_state,row.content,exempted):
                flag = True
                #Filtering Dates
                if filters.from_date and filters.to_date:
                    if not (getdate(filters.from_date) <= row.creation.date() <= getdate(filters.to_date)):
                        flag = False

                if flag:
                    row_data[(row.content).lower().replace(" ", "_")] = time_diff(get_hms(submition_date, row.creation),default_time)
                    row_data["default_time"] += default_time
                    row_data["time_variance"] += time_diff(get_hms(submition_date, row.creation),default_time)
                    row_data["diff"] +=  get_hms(submition_date, row.creation)



            previous_state = row.content
            submition_date = row.creation
        data.append(row_data)

    return columns, data


def get_hms(date1, date2):
    diff_seconds = abs(time_diff_in_seconds(date1, date2))
    return diff_seconds


def check_exempted(state,next_state,exempted):
    for states in exempted:
        if state == states['state'] and next_state == states['next_state']:
            return True
    return False


def time_diff(time_taken,default_duration):
    if not default_duration:
        default_duration = 0

    time_difference =  default_duration - time_taken
    return time_difference