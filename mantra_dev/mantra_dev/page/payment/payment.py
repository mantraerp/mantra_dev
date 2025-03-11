import frappe


@frappe.whitelist()
def select_payment_entry(bank_account):
    # Retrieve mode of payment settings for the provided bank account
    mdf = frappe.db.sql(
        "SELECT mode_of_payment FROM `tabMode of Payment Setting` WHERE parent=%s",
        bank_account,
        as_dict=True
    )
    mode_of_payment = [i["mode_of_payment"] for i in mdf]

    # Query to get payment entries without party name
    sql_query = """
        SELECT 
            name, 
            status, 
            paid_amount,
            base_paid_amount_after_tax,
            party, 
            remarks,
            custom_approved_by,
            reference_no, 
            workflow_state,
            party_name
        FROM `tabPayment Entry`
        WHERE (custom_unique_batch_number IS NULL or custom_unique_batch_number="")
        AND workflow_state = 'Approved'
        AND payment_type = 'Pay'
        AND bank_account = %s
        AND mode_of_payment IN %s
    """
    
    payment_entries = frappe.db.sql(sql_query, (bank_account, tuple(mode_of_payment)), as_dict=True)
    for entry in payment_entries:
        if entry['custom_approved_by']:
            entry['custom_approved_by'] = frappe.db.get_value("User",entry['custom_approved_by'],'full_name')

    return payment_entries






@frappe.whitelist()
def get_salary_slip(payroll_entry):
    
    
    query = "SELECT employee as party,employee_name as party_name,net_pay as base_paid_amount_after_tax,bank_name,bank_account_no,posting_date,name FROM `tabSalary Slip` WHERE `payroll_entry`='{}' AND `docstatus`=1 AND `custom_payment_status` IN ('Fail','Initiated')".format(payroll_entry)
    payment_entries= frappe.db.sql(query,as_dict=1)
    
    # salary_slips = frappe.get_all(
    #         "Salary Slip",
    #         filters={"payroll_entry": payroll_entry,"docstatus": 1} if payroll_entry else {},
    #         fields=["employee", "employee_name", "net_pay", "bank_name", "bank_account_no", "posting_date", "name"]
    #     )

    # payment_entries=[]
    # for salary in salary_slips:
    #     obj = {}
    #     obj['name']=salary['name']
    #     # obj['base_paid_amount_after_tax']=salary['net_pay']
    #     # obj['party']=salary['employee']
    #     obj['remarks']=''
    #     obj['custom_approved_by']=''
    #     obj['reference_no']=''
    #     obj['workflow_state']=''
    #     # obj['party_name']=salary['employee_name']
    #     payment_entries.append(obj)


    return payment_entries


@frappe.whitelist()
def cancel_payment_entries(payment_entry_ids):
    try:
        payment_entry_ids = frappe.parse_json(payment_entry_ids)  # Ensure we get a valid list

        for payment_entry_id in payment_entry_ids:
            # Ensure document exists before modifying it
            if frappe.db.exists("Payment Entry", payment_entry_id):
                frappe.db.set_value("Payment Entry", payment_entry_id, "workflow_state", "Cancelled")
                frappe.db.set_value("Payment Entry", payment_entry_id, "docstatus", 2)

        frappe.db.commit()
        return "Success"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error while canceling Payment Entries")
        return f"An error occurred while canceling payment entries: {str(e)}"
    



import base64

@frappe.whitelist()
def send_excel_email(user_email, filename, filedata, subject):
    """
    Sends an email with the Excel file attached.
    
    :param user_email: Recipient's email address.
    :param filename: The name of the Excel file.
    :param filedata: Base64 encoded file content.
    :param subject: Email subject.
    """
    try:
        # Decode the base64 file data
        decoded_file = base64.b64decode(filedata)
        # Send the email using frappe.sendmail with a proper subject
        frappe.sendmail(
            recipients=[user_email],
            subject=subject,
            message="Please find attached the Excel file containing the payment entry data.",
            attachments=[{
                "fname": filename,
                "fcontent": decoded_file
            }],
            now=True
        )
        return "Email Sent"
    except Exception as e:
        frappe.throw("Failed to send email: " + str(e))


from frappe import _
@frappe.whitelist()
def get_payment_entry_reference_details(payment_entry):
    try:
        payment_entry_doc = frappe.get_doc("Payment Entry", payment_entry)

        def get_approvers(doctype, docname):
            """Fetch unique approvers (emails) from Workflow or Version"""
            workflow_exists = frappe.db.exists("Workflow", {"document_type": doctype})
            approvers = set()

            if workflow_exists:
                approvers.update([
                    row[0] for row in frappe.db.sql(
                        """SELECT DISTINCT comment_email
                        FROM `tabComment`
                        WHERE reference_doctype = %(doctype)s
                        AND reference_name = %(docname)s
                        AND comment_type = 'Workflow'""",
                        {"doctype": doctype, "docname": docname},
                        as_list=True
                    ) if row[0]
                ])
            else:
                approvers.update([
                    row[0] for row in frappe.db.sql(
                        """SELECT DISTINCT modified_by
                        FROM `tabVersion`
                        WHERE ref_doctype = %(doctype)s
                        AND docname = %(docname)s""",
                        {"doctype": doctype, "docname": docname},
                        as_list=True
                    ) if row[0]
                ])

            return approvers

        def get_all_parents(ref_doctype, ref_docname):
            """Get all linked parent documents and their approvers"""
            parents = [(ref_doctype, ref_docname)]
            checked = set()
            approvers_map = {}
            reference_hierarchy = []
            doctype_list = []

            while parents:
                current_doctype, current_docname = parents.pop()

                if (current_doctype, current_docname) in checked:
                    continue   
                checked.add((current_doctype, current_docname))

                reference_hierarchy.append(f"{current_doctype} - {current_docname}")
                if current_doctype not in doctype_list:
                    doctype_list.append(current_doctype)

                doc_approvers = get_approvers(current_doctype, current_docname)
                if doc_approvers:
                    approvers_map[current_doctype] = {
                        "emails": list(doc_approvers),
                        "names": [
                            frappe.db.get_value("User", email, "full_name") or email for email in doc_approvers
                        ]
                    }
                if current_doctype == "Purchase Invoice":
                    purchase_orders = frappe.get_all("Purchase Invoice Item",
                        filters={"parent": current_docname, "purchase_order": ["!=", ""]},
                        fields=["purchase_order"])
                    purchase_receipts = frappe.get_all("Purchase Invoice Item",
                        filters={"parent": current_docname, "purchase_receipt": ["!=", ""]},
                        fields=["purchase_receipt"])

                    for po in purchase_orders:
                        parents.append(("Purchase Order", po["purchase_order"]))
                    for pr in purchase_receipts:
                        parents.append(("Purchase Receipt", pr["purchase_receipt"]))

                elif current_doctype == "Purchase Order":
                    material_requests = frappe.get_all("Purchase Order Item",
                        filters={"parent": current_docname, "material_request": ["!=", ""]},
                        fields=["material_request"])
                    
                    for mr in material_requests:
                        parents.append(("Material Request", mr["material_request"]))

            return reference_hierarchy, doctype_list, approvers_map

        reference_details = []
        if payment_entry_doc.references:
            for ref_row in payment_entry_doc.references:
                ref_doctype = ref_row.get("reference_doctype")
                ref_docname = ref_row.get("reference_name")

                if ref_doctype and ref_docname:
                    reference_hierarchy, doctype_list, approvers_map = get_all_parents(ref_doctype, ref_docname)
                    approvers_list = []
                    approver_names_list = []
                    for doc_type, approvers in approvers_map.items():
                        approvers_list.append(f"{doc_type} Approver - {', '.join(approvers['emails'])}")
                        approver_names_list.extend(approvers["names"])

                    reference_details.append({
                        "Reference ID": ", ".join(reference_hierarchy),
                        "Doctype": ", ".join(doctype_list),  
                        "Approvers": ", ".join(approvers_list),
                        "Approver Names": ", ".join(set(approver_names_list))  
                    })
            custom_details = frappe.get_value("Payment Entry", payment_entry, 
                ["custom_type", "custom_project_type", "remarks","custom_approved_by"], as_dict=True)

            return {
                "reference_details": reference_details,
                "custom_details": custom_details
            }
        else:
            custom_details = frappe.get_value("Payment Entry", payment_entry, 
                ["custom_type", "custom_project_type", "remarks","custom_approved_by"], as_dict=True)
            return {
                "reference_details": reference_details,
                "custom_details": custom_details
            }

    except Exception as e:
        frappe.log_error(f"Error in get_payment_entry_reference_details: {str(e)}")
        return {"error": _("Referenced document could not be fetched.")}