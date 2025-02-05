# Copyright (c) 2024, Software At Work (India) Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import format_datetime, time_diff_in_seconds, getdate, format_duration

def execute(filters=None):
    data = get_data(filters)
    columns = get_columns(filters)
    return columns, data


def get_columns(filters):
    columns = [
        {
            "label": _("DocType"),
            "fieldname": "doctype",
            "fieldtype": "Link",
            "options": "DocType",
            "width": 150,
        },
        {
            "label": _("Document Name"),
            "fieldname": "docname",
            "fieldtype": "Link",
            "options": filters.doctype,
            "width": 200,
        },
    ]
    # for idx in range(max_len):
    columns.extend(
        [
            {
                "label": _("Workflow State"),
                "fieldname": "state_one",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Workflow Submitted Date"),
                "fieldname": "date_sub",
                "fieldtype": "Data",
                "width": 200,
            },
            {
                "label": _("User"),
                "fieldname": "user",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Workflow State"),
                "fieldname": "state_two",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Workflow Change Date"),
                "fieldname": "date_chg",
                "fieldtype": "Data",
                "width": 200,
            },
            # {
            #     "label": _("Default Time"),
            #     "fieldname": "default_time",
            #     "fieldtype": "Duration",
            #     "width": 120,
            # },
            # {
            #     "label": _("Time Taken1"),
            #     "fieldname": "diff",
            #     "fieldtype": "Duration",
            #     "width": 120,
            # },
            # {
            #     "label": _("Time Variance"),
            #     "fieldname": "time_variance",
            #     "fieldtype": "Duration",
            #     "width": 120,
            # },
        ]
    )
    return columns


def get_data(filters):
    #fetch excempted transition
    exempted = []
    workflow = frappe.get_doc("Workflow",{'document_type':filters.doctype,'is_active':1})
    for transition in workflow.transitions:
        if transition.custom_exempted == 1:
            exempted.append({'state':transition.state,'next_state':transition.next_state})
    
    list_filters = {}
    #if filters.from_date and filters.to_date:
    #    list_filters["creation"] = ["between", [filters.from_date, filters.to_date]]
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
        blank_flag = False # show blanck row or not flag end of each doc
        header = {
            "doctype": filters.doctype,
            "docname": name.name,
            "state_one": "Draft",
            "date_sub": format_datetime(name.creation, "MMM dd, yyyy hh:mm:ss a"),
            "user": name.owner
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
        data.append(header)
        for row in row_list:
            row_data = {}
            row_data["state_one"] = previous_state
            row_data["date_sub"] = format_datetime(
                submition_date, "MMM dd, yyyy hh:mm:ss a"
            )
            row_data["date_chg"] = format_datetime(
                row.creation, "MMM dd, yyyy hh:mm:ss a"
            )
            row_data["user"] = row.owner
            row_data["state_two"] = row.content
            default_time = frappe.db.get_value('Workflow Transition',{'parent':workflow.name,"state":previous_state,"next_state":row.content},"custom_default_time") or 0
            # row_data["default_time"] = default_time
            # row_data["time_variance"] = time_diff(get_hms(submition_date, row.creation),default_time)
            # row_data["diff"] =  get_hms(submition_date, row.creation)

            if not check_exempted(previous_state,row.content,exempted):
                flag = True
                #Filtering Dates
                if filters.from_date and filters.to_date:
                    if not (getdate(filters.from_date) <= row.creation.date() <= getdate(filters.to_date)):
                        flag = False
                #Filter Delayed By
                if filters.delayed_by:
                    if row_data["time_variance"]:
                        if not get_flag(filters.delayed_by,-(row_data["time_variance"])):
                            flag = False
                    else:
                        flag = False
                if flag: #Choose adding the row to final data based on filters
                    data.append(header | row_data)
                    blank_flag = True
            previous_state = row.content
            submition_date = row.creation
        data.append({})

    return data


def get_hms(date1, date2):
    diff_seconds = abs(time_diff_in_seconds(date1, date2))
    return diff_seconds


def check_exempted(state,next_state,exempted):
    for states in exempted:
        if state == states['state'] and next_state == states['next_state']:
            return True
    return False


def time_diff(time_taken,default_duration):
    if default_duration == 0:
        return None 

    time_difference =  default_duration - time_taken
    return time_difference

def get_flag(delayed_by,variance):
    
    if variance <= 0:
        return False

    if delayed_by == "<1h" and variance < 3600:
        return True
    
    if delayed_by == "<3h" and variance < 10800:
        return True

    if delayed_by == "<6h" and variance < 21600:
        return True

    if delayed_by == "<9h" and variance < 32400:
        return True
    
    if delayed_by == ">1d" and variance > 86400:
        return True
    
    if delayed_by == ">2d" and variance > 172800:
        return True

    if delayed_by == ">1W" and variance > 604800:
        return True

    if delayed_by == ">1M" and variance > 2592000:
        return True
    
    return False


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_dt_query(doctype, txt, searchfield, start, page_len):
	return frappe.db.sql(
		"""SELECT DISTINCT document_type AS doctype FROM `tabWorkflow` WHERE is_active = 1 AND document_type LIKE %(txt)s LIMIT %(page_len)s OFFSET %(start)s""",
		{"start": start, "page_len": page_len, "txt": "%%%s%%" % txt},
	)

@frappe.whitelist()
def get_average_time_of_workflow_transition(filters):
    import json

    filters = frappe._dict(json.loads(filters))

    # Fetch the active workflow for the given doctype
    workflow = frappe.get_value(
        "Workflow", 
        {"document_type": filters.doctype, "is_active": 1}, 
        "name"
    )
    if not workflow:
        return None

    # Check if the workflow state exists in transitions
    if not frappe.db.exists(
        "Workflow Transition", 
        {"next_state": filters.workflow_state, "parent": workflow}
    ):
        return None
    
    workflow_transition_list = frappe.db.get_all("Workflow Transition", {"parent": workflow}, pluck="next_state")

    # Retrieve document names for the given doctype
    doctype_list = frappe.db.get_list(filters.doctype, pluck="name")
    if not doctype_list:
        return None

    # Construct the SQL query
    conditions = (f"AND c1.reference_name IN {tuple(doctype_list)}" 
        if len(doctype_list) > 1 
        else f"AND c1.reference_name = '{doctype_list[0]}'"
    )

    data_list = frappe.db.sql(
        f"""
        SELECT
            c1.creation AS current_creation_time,
            c1.reference_name,
            COALESCE(
                (
                    SELECT c2.creation
                    FROM `tabComment` as c2
                    WHERE c2.reference_doctype = c1.reference_doctype
                      AND c2.reference_name = c1.reference_name
                      AND c2.creation < c1.creation
                      AND c2.content IN {tuple(workflow_transition_list)}
                    ORDER BY c2.creation DESC
                    LIMIT 1
                ),
                dt.creation
            ) AS last_creation_time
        FROM
            `tabComment` c1
        INNER JOIN
            `tab{filters.doctype}` dt ON dt.name = c1.reference_name
        WHERE
            c1.reference_doctype = %(doctype)s
            AND c1.comment_type = "Workflow"
            AND c1.content = %(workflow_state)s
            {conditions}
        ORDER BY
            c1.creation ASC;
        """,
        {"doctype": filters.doctype, "workflow_state": filters.workflow_state, "conditions": conditions},
        as_dict=1,
    )

    # Calculate the total time and average
    total_time = sum(
        get_hms(entry["last_creation_time"], entry["current_creation_time"])
        for entry in data_list
    )

    average_time = int(total_time) / len(data_list) if data_list else 0

    return {"fieldtype": "Data", "value": str(format_duration(average_time if average_time > 1 else 1))}