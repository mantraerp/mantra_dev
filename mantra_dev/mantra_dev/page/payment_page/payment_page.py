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
            party, 
            reference_no, 
            workflow_state
        FROM `tabPayment Entry`
        WHERE custom_unique_batch_number IS NULL
        AND docstatus = 1
        AND payment_type = 'Pay'
        AND bank_account = %s
        AND mode_of_payment IN %s
    """
    
    payment_entries = frappe.db.sql(sql_query, (bank_account, tuple(mode_of_payment)), as_dict=True)

    # Fetch the party name separately
    for entry in payment_entries:
        party = entry["party"]
        party_name = None

        # Check if the party exists in Supplier
        if frappe.db.exists("Supplier", party):
            party_name = frappe.db.get_value("Supplier", party, "supplier_name")
        
        # Check if the party exists in Customer (if not found in Supplier)
        if not party_name and frappe.db.exists("Customer", party):
            party_name = frappe.db.get_value("Customer", party, "customer_name")

        # Assign the party name to the entry
        entry["party_name"] = party_name if party_name else "Unknown"

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
        error_log=frappe.new_doc("Error Log")
        error_log.error=frappe.as_json({'1':'clcijed'})
        error_log.save()
        # Send the email using frappe.sendmail with a proper subject
        frappe.sendmail(
            recipients=[user_email],
            subject=subject,
            message="Please find attached the Excel file containing the payment data.",
            attachments=[{
                "fname": filename,
                "fcontent": decoded_file
            }],
            now=True
        )
        return "Email Sent"
    except Exception as e:
        frappe.throw("Failed to send email: " + str(e))
