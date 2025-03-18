import frappe
from mantra_dev.mantra_dev.page.payment_page.payment_page import get_payment_entry_reference_details

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