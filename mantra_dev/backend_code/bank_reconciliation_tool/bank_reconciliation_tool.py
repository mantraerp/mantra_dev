import frappe
import json
from frappe.utils import fmt_money




@frappe.whitelist(allow_guest=True)
def match_vouchse():
    # bank_transcation = "SELECT bt.name as bank_transcation, pe.name FROM `tabBank Transaction` AS bt LEFT JOIN `tabPayment Entry` AS pe ON pe.custom_reco_remarks = bt.description WHERE pe.docstatus=1 AND bt.status='Unreconciled'"
    bank_transcation_query = "SELECT name, description, deposit, withdrawal FROM `tabBank Transaction` WHERE `docstatus`=1 AND `status`='Unreconciled'"
    bank_transcation = frappe.db.sql(bank_transcation_query, as_dict=True)
    for bt in bank_transcation:
        payment_entry_query = f"""
            SELECT 
                pe.name, 
                pe.paid_amount 
            FROM `tabPayment Entry` as pe 
            WHERE 
                pe.docstatus = 1 
                AND pe.workflow_state = 'Approved' 
                AND NOT EXISTS (
                    SELECT 1 FROM `tabBank Transaction Payments` AS btp
                    WHERE btp.payment_entry = pe.name
                    AND btp.docstatus = 1
                    AND btp.payment_document = 'Payment Entry'
                    AND btp.allocated_amount = pe.paid_amount
                ) 
                AND pe.custom_reco_remarks = '{bt['description']}'
        """

        if bt['deposit'] > 0:
            payment_entry_query += " AND pe.payment_type = 'Receive'"
        elif bt['withdrawal'] > 0:
            payment_entry_query += " AND pe.payment_type = 'Pay'"


        payment_entry = frappe.db.sql(payment_entry_query, as_dict=True)
        final_payment_entry = []
        for pe in payment_entry:
            obj={}
            obj['payment_doctype']='Payment Entry'
            obj['payment_name']=pe['name']
            obj['amount']='{}'.format(fmt_money(pe['paid_amount'], currency="INR"))
            final_payment_entry.append(obj)

        if len(final_payment_entry)!=0:
            frappe.enqueue(reconcile_vouchers, queue='long', timeout=3600,bank_transaction_name=bt['name'],vouchers=json.dumps(final_payment_entry)) 

@frappe.whitelist(allow_guest=True)
def reconcile_vouchers(bank_transaction_name,  vouchers):
    # updated clear date of all the vouchers based on the bank transaction
    vouchers = json.loads(vouchers)

    transaction = frappe.get_doc("Bank Transaction", bank_transaction_name)
    transaction.add_payment_entries(vouchers)
    transaction.validate_duplicate_references()
    transaction.allocate_payment_entries()
    transaction.update_allocated_amount()
    transaction.set_status()
    transaction.save()

    return transaction