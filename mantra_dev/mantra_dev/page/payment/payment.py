import frappe # type: ignore

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
        ORDER BY party_name ASC
    """
    
    payment_entries = frappe.db.sql(sql_query, (bank_account, tuple(mode_of_payment)), as_dict=True)
    return payment_entries
    
@frappe.whitelist()
def get_salary_slip(payroll_entry):
    query = """
        SELECT 
            employee AS party,
            employee_name AS party_name,
            net_pay AS base_paid_amount_after_tax,
            bank_name,
            bank_account_no,
            posting_date,
            name 
        FROM `tabSalary Slip` 
        WHERE payroll_entry = %s 
            AND docstatus = 1 
            AND custom_payment_status != 'Success'
    """
    
    payment_entries = frappe.db.sql(query, (payroll_entry,), as_dict=True)
    
    return payment_entries


@frappe.whitelist()
def cancel_payment_entries(payment_entry_ids):
    try:
        payment_entry_ids = frappe.parse_json(payment_entry_ids)  # Ensure we get a valid list

        for payment_entry_id in payment_entry_ids:
            # Ensure document exists before modifying it
            if frappe.db.exists("Payment Entry", payment_entry_id):
                frappe.db.set_value("Payment Entry", payment_entry_id, "workflow_state", "Cancelled")    
                current_user = frappe.session.user
                frappe.set_user("Administrator")
                doc = frappe.get_doc("Payment Entry",payment_entry_id)
                doc.cancel()
                frappe.set_user(current_user)
                
        # frappe.db.commit()
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

        def get_approvals_and_attachments(doctype, docname):
            approvals = []
            attachments = []

            # Fetch comments where comment_type is 'Workflow' or 'Label'
            comments = frappe.db.sql("""
                SELECT comment_email, content, comment_by, comment_type 
                FROM `tabComment`
                WHERE reference_doctype = %(doctype)s 
                AND reference_name = %(docname)s 
                AND comment_type IN ('Workflow', 'Label') 
                ORDER BY creation ASC
            """, {"doctype": doctype, "docname": docname}, as_dict=True)

            # Handle different document types
            created_by = frappe.get_doc("User", frappe.db.get_value(doctype, docname, "owner")).full_name

            # Ensure Created By is added only once
            if not any('Created By' in approval for approval in approvals):
                approvals.append(f"Created By: {created_by}")

            # Create a set to track already added users for each approval type
            added_approvers = {
                "Reviewed By": set(),
                "Approved By": set(),
                "Verified By": set(),
                "Approval By": set(),
                "Validated By": set(),
                "Audited By": set(),
                "Submitted By": set(),
                "Pending By":set()
            }

            # Handle different document types
            if doctype == "Purchase Order" and comments:
                for comment in comments:
                    if 'Reviewed' in comment['content']:
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Reviewed By"]:
                            approvals.append(f"Reviewed By: {user.full_name}")
                            added_approvers["Reviewed By"].add(user.full_name)
                    elif 'Approved' in comment['content']:
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Approved By"]:
                            approvals.append(f"Approved By: {user.full_name}")
                            added_approvers["Approved By"].add(user.full_name)

            elif doctype == "Purchase Receipt" and comments:
                for comment in comments:
                    if 'Approved' in comment['content']:
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Approved By"]:
                            approvals.append(f"Approved By: {user.full_name}")
                            added_approvers["Approved By"].add(user.full_name)

            elif doctype == "Purchase Invoice" and comments:
                for comment in comments:
                    if 'To Approve' in comment['content']:  # Verified By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Verified By"]:
                            approvals.append(f"Verified By: {user.full_name}")
                            added_approvers["Verified By"].add(user.full_name)
                    elif 'Validation' in comment['content']:  # Approval By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Approval By"]:
                            approvals.append(f"Approval By: {user.full_name}")
                            added_approvers["Approval By"].add(user.full_name)
                    elif '2nd Validation' in comment['content']:  # Validated By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Validated By"]:
                            approvals.append(f"Validated By: {user.full_name}")
                            added_approvers["Validated By"].add(user.full_name)
                    elif 'Review' in comment['content']:  # Audited By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Audited By"]:
                            approvals.append(f"Audited By: {user.full_name}")
                            added_approvers["Audited By"].add(user.full_name)
                    elif 'Checked' in comment['content']:  # Reviewed By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Reviewed By"]:
                            approvals.append(f"Reviewed By: {user.full_name}")
                            added_approvers["Reviewed By"].add(user.full_name)
                    elif 'Approved' in comment['content']:  # Submitted By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Submitted By"]:
                            approvals.append(f"Submitted By: {user.full_name}")
                            added_approvers["Submitted By"].add(user.full_name)

            elif doctype == "Material Request" and comments:
                for comment in comments:
                    if 'To Approve' in comment['content']:  # Verified By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Verified By"]:
                            approvals.append(f"Verified By: {user.full_name}")
                            added_approvers["Verified By"].add(user.full_name)
                    elif 'Validation' in comment['content']:  # Approval By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Approval By"]:
                            approvals.append(f"Approval By: {user.full_name}")
                            added_approvers["Approval By"].add(user.full_name)
                    elif '2nd Validation' in comment['content']:  # Validated By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Validated By"]:
                            approvals.append(f"Validated By: {user.full_name}")
                            added_approvers["Validated By"].add(user.full_name)
                    elif 'Review' in comment['content']:  # Audited By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Audited By"]:
                            approvals.append(f"Audited By: {user.full_name}")
                            added_approvers["Audited By"].add(user.full_name)
                    elif 'Checked' in comment['content']:  # Reviewed By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Reviewed By"]:
                            approvals.append(f"Reviewed By: {user.full_name}")
                            added_approvers["Reviewed By"].add(user.full_name)
                    elif 'Approved' in comment['content']:  # Submitted By
                        user = frappe.get_doc("User", comment['comment_email'])
                        if user.full_name not in added_approvers["Submitted By"]:
                            approvals.append(f"Submitted By: {user.full_name}")
                            added_approvers["Submitted By"].add(user.full_name)

            else:
                if comments:
                    for comment in comments:
                        user = frappe.get_doc("User", comment['comment_email'])

                        # Check if content exists in added_approvers keys
                        if comment['content'] in added_approvers:
                            if user.full_name not in added_approvers[comment['content']]:
                                approvals.append(f"{comment['content']} by: {user.full_name}")
                                added_approvers[comment['content']].add(user.full_name)
                        else:
                            # Handle unknown approval statuses gracefully
                            approvals.append(f"{comment['content']} by: {user.full_name}")
            # Fetch file attachments related to the document
            file_attachments = frappe.db.sql("""
                SELECT file_url FROM `tabFile`
                WHERE attached_to_doctype = %(doctype)s AND attached_to_name = %(docname)s
            """, {"doctype": doctype, "docname": docname}, as_dict=True)

            attachments = [file.file_url for file in file_attachments]

            return approvals, attachments

        reference_details = []

        if payment_entry_doc.references:
            for ref_row in payment_entry_doc.references:
                ref_doctype = ref_row.get("reference_doctype")
                ref_docname = ref_row.get("reference_name")

                # Handling "Purchase Invoice" references
                if ref_doctype == "Purchase Invoice":
                    po_doc = frappe.db.sql("""
                        SELECT DISTINCT purchase_order FROM `tabPurchase Invoice Item`
                        WHERE parent = %s AND purchase_order IS NOT NULL
                        LIMIT 1
                    """, (ref_docname,), as_dict=True)

                    pr_doc = frappe.db.sql("""
                        SELECT DISTINCT purchase_receipt FROM `tabPurchase Invoice Item`
                        WHERE parent = %s AND purchase_receipt IS NOT NULL
                        LIMIT 1
                    """, (ref_docname,), as_dict=True)

                    po_name = po_doc[0]["purchase_order"] if po_doc else None
                    po_approval_form = frappe.db.sql("""
                        SELECT name FROM `tabPO Form Approval`
                        WHERE purchase_order = %s
                        LIMIT 1
                    """, (po_name,), as_dict=True)

                    po_approval_form_name = po_approval_form[0]["name"] if po_approval_form else ""
                    pr_name = pr_doc[0]["purchase_receipt"] if pr_doc else None

                    mr_doc = None
                    if po_name:
                        mr_doc = frappe.db.sql("""
                            SELECT DISTINCT material_request FROM `tabPurchase Order Item`
                            WHERE parent = %s AND material_request IS NOT NULL
                            LIMIT 1
                        """, (po_name,), as_dict=True)

                    mr_name = mr_doc[0]["material_request"] if mr_doc else None

                    related_docs = [{"doctype": "Purchase Invoice", "docname": ref_docname}]
                    if pr_name:
                        related_docs.append({"doctype": "Purchase Receipt", "docname": pr_name})
                    if po_name:
                        related_docs.append({"doctype": "Purchase Order", "docname": po_name})
                    if mr_name:
                        related_docs.append({"doctype": "Material Request", "docname": mr_name})

                    for doc in related_docs:
                        docname = doc["docname"]
                        doctype = doc["doctype"]

                        approvals, attachments = get_approvals_and_attachments(doctype, docname)
                     


                        purpose = frappe.db.get_value(doctype, docname, "custom_purpose") if doctype in ["Purchase Order","Purchase Invoice"] else \
                                  frappe.db.get_value(doctype, docname, "material_request_type") if doctype == "Material Request" else ""

                        created_on, submitted_on = frappe.db.get_value(doctype, docname, ["creation", "modified"]) or (None, None)
                        created_on = frappe.utils.formatdate(created_on, "dd/MM/yyyy") if created_on else ""
                        submitted_on = frappe.utils.formatdate(submitted_on, "dd/MM/yyyy") if submitted_on else ""

                        reference_details.append({
                            "Document ID": f"{doctype}",
                            "Document": docname,
                            "Created On": created_on,
                            "Submitted On": submitted_on,
                            "Purpose": purpose,
                            "doctype": doctype,
                            "Po Approval":po_approval_form_name,
                            "Approvers": "<br>".join(approvals) if approvals else "No Approvers",
                            "Attachments": ", ".join(attachments) if attachments else ""
                        })

                # Handling "Expense Claim" references
                elif ref_doctype == "Expense Claim":
                    expense_claim_details = frappe.db.sql("""
                        SELECT name, employee, status FROM `tabExpense Claim`
                        WHERE name = %s
                    """, (ref_docname,), as_dict=True)

                    expense_claim = expense_claim_details[0] if expense_claim_details else None
                    created_on, submitted_on = frappe.db.get_value(ref_doctype, ref_docname, ["creation", "modified"]) or (None, None)
                    created_on = frappe.utils.formatdate(created_on, "dd/MM/yyyy") if created_on else ""
                    submitted_on = frappe.utils.formatdate(submitted_on, "dd/MM/yyyy") if submitted_on else ""
                    if expense_claim:
                        employee = frappe.db.get_value("Employee", expense_claim["employee"], "employee_name")
                        approvals, attachments = get_approvals_and_attachments("Expense Claim", ref_docname)

                        reference_details.append({
                            "Document ID": "Expense Claim",
                            "Document": ref_docname,
                            "doctype": ref_doctype,
                            "Created On": created_on,
                            "Submitted On": submitted_on,
                            "Employee": employee,
                            "Status": expense_claim["status"],
                            "Approvers": "<br>".join(approvals) if approvals else "No Approvers",
                            "Attachments": ", ".join(attachments) if attachments else ""
                        })

                # Handling "Employee Advance" references
                elif ref_doctype == "Employee Advance":
                    employee_advance_details = frappe.db.sql("""
                        SELECT name, employee, advance_amount,purpose, status FROM `tabEmployee Advance`
                        WHERE name = %s
                    """, (ref_docname,), as_dict=True)

                    employee_advance = employee_advance_details[0] if employee_advance_details else None
                    created_on, submitted_on = frappe.db.get_value(ref_doctype, ref_docname, ["creation", "modified"]) or (None, None)
                    created_on = frappe.utils.formatdate(created_on, "dd/MM/yyyy") if created_on else ""
                    submitted_on = frappe.utils.formatdate(submitted_on, "dd/MM/yyyy") if submitted_on else ""
                    if employee_advance:
                        employee = frappe.db.get_value("Employee", employee_advance["employee"], "employee_name")
                        approvals, attachments = get_approvals_and_attachments("Employee Advance", ref_docname)

                        reference_details.append({
                            "Document ID": "Employee Advance",
                            "Document": ref_docname,
                            "doctype": ref_doctype,
                            "Employee": employee,
                            "Amount Approved": employee_advance["advance_amount"],
                            "Created On": created_on,
                            "Submitted On": submitted_on,
                            "Status": employee_advance["status"],
                            "Purpose": employee_advance['purpose'],
                            "Approvers": "<br>".join(approvals) if approvals else "No Approvers",
                            "Attachments": ", ".join(attachments) if attachments else ""
                        })

                elif ref_doctype == "Purchase Order":
                    po_name = ref_docname
                  
                    po_approval_form = frappe.db.sql("""
                        SELECT name FROM `tabPO Form Approval`
                        WHERE purchase_order = %s
                        LIMIT 1
                    """, (po_name,), as_dict=True)

                    po_approval_form_name = po_approval_form[0]["name"] if po_approval_form else ""

                    # Fetch Material Request related to the Purchase Order
                    mr_doc = frappe.db.sql("""
                        SELECT DISTINCT material_request FROM `tabPurchase Order Item`
                        WHERE parent = %s AND material_request IS NOT NULL
                        LIMIT 1
                    """, (po_name,), as_dict=True)

                    mr_name = mr_doc[0]["material_request"] if mr_doc else None

                    related_docs = [{"doctype": "Purchase Order", "docname": ref_docname}]
                    if mr_name:
                        related_docs.append({"doctype": "Material Request", "docname": mr_name})

                    for doc in related_docs:
                        docname = doc["docname"]
                        doctype = doc["doctype"]

                        approvals, attachments = get_approvals_and_attachments(doctype, docname)

                        purpose = frappe.db.get_value(doctype, docname, "custom_purpose") if doctype in ["Purchase Order","Purchase Invoice"] else \
                                  frappe.db.get_value(doctype, docname, "material_request_type") if doctype == "Material Request" else ""

                        created_on, submitted_on = frappe.db.get_value(doctype, docname, ["creation", "modified"]) or (None, None)
                        created_on = frappe.utils.formatdate(created_on, "dd/MM/yyyy") if created_on else ""
                        submitted_on = frappe.utils.formatdate(submitted_on, "dd/MM/yyyy") if submitted_on else ""

                        reference_details.append({
                            "Document ID": f"{doctype}",
                            "Document": docname,
                            "Created On": created_on,
                            "Submitted On": submitted_on,
                            "Purpose": purpose,
                            "doctype": doctype,
                            "Po Approval":po_approval_form_name,
                            "Approvers": "<br>".join(approvals) if approvals else "No Approvers",
                            "Attachments": ", ".join(attachments) if attachments else ""
                        })

        reference_details.reverse()

        custom_details = frappe.get_value("Payment Entry", payment_entry, 
            ["custom_type", "custom_project_type", "remarks", "custom_approved_by"], as_dict=True)

        return {
            "reference_details": reference_details,
            "custom_details": custom_details
        }

    except Exception as e:
        frappe.log_error(f"Error in get_payment_entry_reference_details: {str(e)}")
        return {"error": _(f"Error fetching approval details: {str(e)}")}
