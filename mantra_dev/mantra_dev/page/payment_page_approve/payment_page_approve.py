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
            reference_no, 
            remarks,
            custom_approved_by,
            workflow_state,
            party_name
        FROM `tabPayment Entry`
        WHERE (custom_unique_batch_number IS NULL or custom_unique_batch_number="")
        AND workflow_state = 'Checked'
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
def approve_payment_entries(payment_entry_ids):
    try:
        payment_entry_ids = frappe.parse_json(payment_entry_ids)  # Ensure we get a valid list

        for payment_entry_id in payment_entry_ids:
            # Ensure document exists before modifying it
            if frappe.db.exists("Payment Entry", payment_entry_id):
                frappe.db.set_value("Payment Entry", payment_entry_id, "workflow_state", "Approved")
                frappe.db.set_value("Payment Entry", payment_entry_id, "docstatus", 1)

        frappe.db.commit()
        return "Success"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error while canceling Payment Entries")
        return f"An error occurred while canceling payment entries: {str(e)}"
    


@frappe.whitelist()
def hold_payment_entries(payment_entry_ids):
    try:
        payment_entry_ids = frappe.parse_json(payment_entry_ids)  # Ensure we get a valid list

        for payment_entry_id in payment_entry_ids:
            # Ensure document exists before modifying it
            if frappe.db.exists("Payment Entry", payment_entry_id):
                frappe.db.set_value("Payment Entry", payment_entry_id, "workflow_state", "On Hold")
                frappe.db.set_value("Payment Entry", payment_entry_id, "docstatus", 1)

        frappe.db.commit()
        return "Success"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error while canceling Payment Entries")
        return f"An error occurred while canceling payment entries: {str(e)}"
