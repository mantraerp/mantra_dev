import frappe # type: ignore
import num2words # type: ignore
import random
import shutil
from frappe.email.email_body import get_pdf  # type: ignore
import os
import csv
import json
from frappe.utils import now # type: ignore
from frappe.email.queue import flush # type: ignore
from datetime import datetime, timedelta
from frappe.core.doctype.activity_log.activity_log import add_authentication_log # type: ignore
from frappe.auth import LoginManager # type: ignore
import string
import ast
from cryptography.fernet import Fernet # type: ignore
import requests # type: ignore
from datetime import datetime
import traceback
from num2words import num2words # type: ignore
from mantra_dev.backend_code.globle import errorLog,errorLogExites # type: ignore
import subprocess

@frappe.whitelist(allow_guest=True)
def select_payment_entry_test():
    
    reply = {}
    folder_path = "/home/mantra/mantrastage-bench/ShellScript/"  # Change this to your actual path
    script_name = "give_write_permission.sh"
    
    
    
    # password = "E&rp@_5546"
    # command = f"echo {password} | sudo -S sh give_write_permission.sh"

    # # subprocess.run(command, cwd="/path/to/script", shell=True)
    
    try:
        result = subprocess.run(["sh", script_name], cwd=folder_path, capture_output=True, text=True, check=True)
        reply['result.stdout']=result.stdout
        reply['result.stderr']=result.stderr
    except subprocess.CalledProcessError as e:
        reply['result.stdout']=e.stdout
        reply['result.stderr']=e.stderr        
    except FileNotFoundError:
        reply['error']=f"Error: The folder '{folder_path}' or script '{script_name}' was not found." 
    
    # # subprocess.run(["sh", "give_write_permission.sh"], cwd="/home/mantra/mantrastage-bench/ShellScript", shell=True)
    
    # # os.popen('sh /home/mantra/mantrastage-bench/ShellScript/give_write_permission.sh')
    return reply
    
    bank_account = "Mantra - ICICI Bank Limited - 018951000027"
    doc1 = frappe.get_single("Bank Authentication")

    mdf=frappe.db.sql("select mode_of_payment,abbrivation from `tabMode of Payment Setting` where parent=%s",bank_account,as_dict=True)
    mode_of_payment=[]
    for i in mdf:
        mode_of_payment.append(i["mode_of_payment"])

    sql_query = """
        SELECT name, base_paid_amount_after_tax
        FROM `tabPayment Entry`
        WHERE custom_unique_batch_number IS NULL
        AND docstatus=1
        AND payment_type='Pay'
        AND bank_account=%s
        AND mode_of_payment IN %s
    """
    
    # Execute the query and fetch results as dictionaries
    payment_entry = frappe.db.sql(sql_query, (bank_account, tuple(mode_of_payment)), as_dict=True)
 
    if payment_entry:
        payment_entry_list=[]
        for i in payment_entry:
            payment_entry_list.append(i['name'])

        if frappe.db.get_value("Bank Integration", bank_account, "bank")=="ICICI Bank Limited":
            return icici_file_create(bank_account,payment_entry_list)

        return "Bank not found"
    else:
        return {"payment_entry_list":[],"amount":0}

#this function is use for a push file in icici snorken folder 
def icici_file_create(bank_account, payment_entry_list):
    
    try :
        directory = '/home/mantra/Desktop/TestPayment'
        header = [
            'Debit Ac No', 'beneficiary code', 'Beneficiary Ac No', 'Beneficiary Name',
            'Amt', 'Pay Mod', 'Date', 'IFSC', 'Payable Location name', 'Print Location',
            'Bene Mobile no', 'Bene email id', 'Ben add1', 'Ben add2', 'Ben add3',
            'Ben add4', 'Add details 1', 'Add details 2', 'Add details 3',
            'Add details 4', 'Add details 5', 'Remarks'
        ]
        
        #distribute payment entry based on vendor code
        vendor_payment_entry={}
        for i in payment_entry_list:
            payment_entry = frappe.get_doc("Payment Entry", i)
            all_vendor = vendor_payment_entry.keys()
            
            if payment_entry.party in all_vendor:
                party_payment_list = vendor_payment_entry[payment_entry.party]
                party_payment_list.append(payment_entry)
            else:
                vendor_payment_entry[payment_entry.party] = [payment_entry]


        all_vendor = vendor_payment_entry.keys()
        for vendor in all_vendor:
            party_payment_list = vendor_payment_entry[vendor]
            
            total_amount = 0
            data_rows = []
            for payment_entry in party_payment_list:
                mdf = frappe.db.sql("""
                    SELECT mode_of_payment, abbrivation 
                    FROM `tabMode of Payment Setting` 
                    WHERE parent=%s AND mode_of_payment=%s
                """, (bank_account, payment_entry.mode_of_payment), as_dict=True)


                debit_ac_no = frappe.db.get_value("Bank Account", payment_entry.bank_account, "bank_account_no") or ""
                beneficiary_code = payment_entry.party or ""
                beneficiary_ac_no = frappe.db.get_value("Bank Account", payment_entry.party_bank_account, "bank_account_no") or ""
                beneficiary_name = payment_entry.party_name or ""
                amt = payment_entry.base_paid_amount_after_tax
                pay_mod = mdf[0]["abbrivation"] if mdf else ""
                payable_location_name = ""
                print_location = ""
                input_date = payment_entry.posting_date.strftime('%Y-%m-%d')
                date = datetime.today().strftime('%d-%b-%Y')
                # date = datetime.strptime(input_date, "%Y-%m-%d").strftime("%d-%b-%Y")
                remarks = payment_entry.remarks.replace('\n', ' ') if payment_entry.remarks else ""
                ifsc = frappe.db.get_value("Bank Account", payment_entry.party_bank_account, "custom_ifsc") or ""

                total_amount += amt
                
                bane_mobile_no = ""
                bane_email_id = ""
                bane_add1 = ""
                bane_add2 = ""
                bane_add3 = ""
                bane_add4 = ""
                
                # bane_add_detail_1 = unique_batch_number
                bane_add_detail_1 = payment_entry.name
                bane_add_detail_2 = ""
                bane_add_detail_3 = ""
                bane_add_detail_4 = ""
                bane_add_detail_5 = ""
                
                new_row = [
                    debit_ac_no, beneficiary_code, beneficiary_ac_no, beneficiary_name,
                    amt, pay_mod, date, ifsc, payable_location_name, print_location,
                    bane_mobile_no, bane_email_id, bane_add1, bane_add2, bane_add3,
                    bane_add4, bane_add_detail_1, bane_add_detail_2, bane_add_detail_3,bane_add_detail_4,bane_add_detail_5, remarks
                ]
                data_rows.append(new_row)

            if total_amount <= 500000:


                numeric_characters = string.digits
                unique_batch_number = ''.join(random.choices(numeric_characters, k=6))

                current_date = datetime.now()
                formatted_date = current_date.strftime("%d%m%Y")
                
                uid = os.getuid()
                gid = os.getgid()

                # Change ownership to the current user
                # os.chown(directory, uid, gid)
                # os.chmod(directory, 777)
                os.popen('sh /home/mantra/mantrastage-bench/ShellScript/give_write_permission.sh')
                
                file_name = f"MANTRASH2H_MANTRASH2HUP_{formatted_date}_{unique_batch_number}.txt"
                file_path = os.path.join(directory, file_name)


                for payment_entry in party_payment_list:
                    #Update value in payment entry
                    update_query = "UPDATE `tabPayment Entry` SET `custom_payment_file_name`='{}' WHERE `name`='{}'".format(file_name,payment_entry.name)


                
                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file, delimiter="|")
                    writer.writerow(header)
                    writer.writerows(data_rows)

                # os.popen('sh /home/mantra/mantrastage-bench/ShellScript/give_read_permission.sh')

                # old_umask = os.umask(0)
                
                # try:
                #     #Write file in bank folder
                #     with open(file_path, 'w', newline='') as file:
                #         writer = csv.writer(file, delimiter="|")
                #         writer.writerow(header)
                #         writer.writerows(data_rows)
                # finally:
                #     os.umask(old_umask)
                    
                    
        # frappe.db.commit()
        return "Done"
    except Exception as e :
        frappe.sendmail(
            recipients=["ravi.patel@mantratec.com"],
            subject="Payment file create error",
            message="File name : banck_transaction Method Name: icici_file_create <br><br>{}".format(str(traceback.format_exc())),
        )
        return str(traceback.format_exc())