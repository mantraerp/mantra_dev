import frappe # type: ignore
import json
from datetime import datetime, timedelta
from frappe.utils import format_duration, flt, fmt_money # type: ignore
from mantra_dev.mantra_dev.report.workflow_tat_report.workflow_tat_report import time_diff, get_hms # type: ignore
from frappe.utils.nestedset import get_descendants_of # type: ignore

@frappe.whitelist(allow_guest=True)
def get_average_time_of_workflow_transition(filters):
    # This Fuction Passed filter of company, workflow_state, doctype
    # Return the average time taken for that status

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

    doctype_list = frappe.db.get_list(filters.doctype, pluck="name")
    if not doctype_list:
        return None

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
                      AND c2.comment_type = "Workflow"
                      AND c2.creation < c1.creation
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
    average_time = int(total_time) / (len(data_list) if data_list else 0)

    return str(format_duration(average_time if average_time > 1 else 1))


@frappe.whitelist(allow_guest=True)
def get_average_time_of_doctype_list(month, year, doctype, date_field):
    # Give Month and year with doctype name then return the average time taken by the process of that month
    # Return Default Time, Time Taken, Diff

    month = datetime.strptime(month, "%b").month
    year = int(year)

    first_date = datetime(year, month, 1).date()
    last_date = (datetime(year, month + 1, 1) - timedelta(days=1)).date() if month < 12 else datetime(year, 12, 31).date()

    try:
        doctype_list = frappe.db.get_all(doctype, filters={date_field: ["between", [first_date, last_date]]}, pluck="name")


        if not doctype_list:
            return "No records found for the given month and year."

        total_time = 0
        for docname in doctype_list:
            data = get_doc_workflow_average_time(doctype, docname)
            if "time_variance" not in data:
                return data
            total_time += data["time_variance"]

        if total_time > 1:
            format_time = format_duration(round(total_time/len(doctype_list)) or 1)
        elif total_time < 0:
            format_time = "- " + format_duration(round(total_time*-1/len(doctype_list)) or 1)
        else:
            format_time = None

        return format_time
    except Exception as e:
        frappe.log_error("get_average_time_of_doctype_list", str(e))


@frappe.whitelist(allow_guest=True)
def get_doc_workflow_average_time(doctype, docname, format_time=False):
    # Give doctype name and doctype with format_time or not then return the average time taken by the process of that doctype
    # Return Default Time, Time Taken, Time Taken

    data_list = {
        "default_time": 0,
        "time_variance": 0,
        "time_taken": 0
    }
    creation_time = frappe.db.get_value(doctype, docname, "creation")
    try:
        workflow = frappe.get_doc("Workflow",{'document_type': doctype,'is_active':1})

        if not workflow:
            return "Workflow Not Found"

        workflow_state = workflow.states[0].state

        # Workflow State wise default timing store in dict with state and next_state key
        workflow_transitions_list = {}
        for transition in workflow.transitions:
            if not f'{transition.state}_{transition.next_state}' in workflow_transitions_list:
                workflow_transitions_list[f'{transition.state}_{transition.next_state}'] = transition.custom_default_time

        sql_list = frappe.db.sql(
            """SELECT
                content,
                creation
            FROM
                `tabComment`
            WHERE
                reference_doctype = %(doctype)s
                AND reference_name = %(docname)s
                AND comment_type = "Workflow"
            ORDER BY
                creation ASC;""",
            {"doctype": doctype, "docname": docname},
            as_dict=1,
        )

        # Retrieve a list of all workflow change logs from the database for that doc, including content and creation time
        for data in sql_list:
            default_time = workflow_transitions_list[f"{workflow_state}_{data.content}"]
            data_list["default_time"] += int(default_time)
            data_list["time_variance"] += int(time_diff(get_hms(creation_time, data.creation),default_time)) * -1
            data_list["time_taken"] +=  int(get_hms(creation_time, data.creation))
            workflow_state = data.content
            creation_time = data.creation

        # If displaying time in a specific doctype form, format the time first and then return the formatted time
        if format_time:
            for key in ["default_time", "time_variance", "time_taken"]:
                if data_list[key] != 0:
                    if key == 'time_variance' and data_list[key] < 0:
                        data_list[key] = "- " + format_duration(data_list[key] * -1)
                    else:
                        data_list[key] = format_duration(data_list[key])

        return data_list

    except Exception as e:
        frappe.log_error("get_doc_workflow_average_time", str(e))


@frappe.whitelist(allow_guest=True)
def get_current_total_value_of_stock_based_on_stock_category(filters):
    filters = frappe._dict(json.loads(filters))

    item_list = frappe.db.get_all("Item", {'custom_stock_category': filters.stock_category}, pluck="name")
    if item_list:
        conditions = ""
        if len(item_list) == 1:
            conditions = f"AND b.item_code = '{item_list[0]}'"
        else:
            conditions = f"AND b.item_code IN {tuple(item_list)}"

        query = f"""
            SELECT valuation_rate
            FROM (
                SELECT 
                    SUM(b.actual_qty * b.valuation_rate) AS valuation_rate,
                    COUNT(DISTINCT b.item_code) AS item_count
                FROM
                    `tabBin` AS b
                WHERE 
                    b.actual_qty > 0
                    {conditions}
            ) AS subquery
            WHERE item_count > 0
        """

        result = frappe.db.sql(query, {"conditions": conditions}, as_dict=1)
        if result:
            return fmt_money(result[0].get("valuation_rate"), currency="INR")
        else:
            return None

    else:
        return None


@frappe.whitelist(allow_guest=True)
def get_current_total_value_of_stock_based_on_item_group(filters):
    filters = frappe._dict(json.loads(filters))
    descendants = get_descendants_of("Item Group", filters.item_group)
    item_list = frappe.db.get_all("Item", {'item_group':  ["in", descendants]}, pluck="name")
    # item_list = frappe.db.get_all("Item", {'item_group': filters.item_group}, pluck="name")
    if item_list:
        conditions = ""
        if len(item_list) == 1:
            conditions = f"AND b.item_code = '{item_list[0]}'"
        else:
            conditions = f"AND b.item_code IN {tuple(item_list)}"

        query = f"""
            SELECT valuation_rate
            FROM (
                SELECT 
                    SUM(b.actual_qty * b.valuation_rate) AS valuation_rate,
                    COUNT(DISTINCT b.item_code) AS item_count
                FROM
                    `tabBin` AS b
                WHERE 
                    b.actual_qty > 0
                    {conditions}
            ) AS subquery
            WHERE item_count > 0
        """

        result = frappe.db.sql(query, {"conditions": conditions}, as_dict=1)
        if result:
            return fmt_money(result[0].get("valuation_rate"), currency="INR")
        else:
            return None

    else:
        return None