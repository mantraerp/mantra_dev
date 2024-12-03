import frappe
import random
import shutil
from frappe.utils import flt, nowdate
import os
import csv
import glob
import json
from frappe.utils import now
from frappe.email.queue import flush
from datetime import datetime, timedelta
from frappe.core.doctype.activity_log.activity_log import add_authentication_log
from frappe.auth import LoginManager
import string
import ast
from cryptography.fernet import Fernet
import requests
from datetime import datetime

@frappe.whitelist()
# Upload Approved Beneficiary file on Snorkel with Indicator A
def upload_beneficiary_file(doc_name):
    try:

        numeric_characters = string.digits
        unique_batch_number = ''.join(random.choices(numeric_characters, k=6))

        current_date = datetime.now()
        formatted_date = current_date.strftime("%d%m%Y")

        file_name = f"MANTRASH2H_MANTRABENH2HUP_{formatted_date}_{unique_batch_number}.txt"

        directory_sql = """
            SELECT beneficiary_file_upload_path
            FROM `tabBank Integration`
            WHERE upload_beneficiary_file = 1
        """

        directory_list = frappe.db.sql(directory_sql, as_dict=True) 
        # directory_list = frappe.db.get_list("Bank Integration", filters={'upload_beneficiary_file':1}, fields=["beneficiary_file_upload_path"])

        if not directory_list:
            frappe.throw("Upload beneficiary file path not set in 'Bank Integration'")

        directory = directory_list[0].get("beneficiary_file_upload_path")

        if not directory:
            frappe.throw("Upload beneficiary file path not set in 'Bank Integration'")

        file_path = os.path.join('/home/mantra/ICICI_Bank_integration/epayments/beneupload', file_name)
        file_path2 = os.path.join('/home/mantra/Desktop', file_name)

        header = [
                'Indicator','Beneficiary Code','Beneficiary Name','Beneficiary IFSC','Beneficiary Account No','Beneficiary Address'
            ]

        bank_account = frappe.get_doc("Bank Account", doc_name)

        data_rows = [[
            "A",  # Indicator
            bank_account.party,  # Beneficiary Code
            bank_account.account_name,  # Beneficiary Name
            bank_account.custom_ifsc,  # Beneficiary IFSC
            bank_account.bank_account_no,  # Beneficiary Account No
            bank_account.custom_branch_location  # Beneficiary Address
        ]]

        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow(header)
            writer.writerows(data_rows) 

        with open(file_path, 'rb') as file:
            file_content = file.read()

        with open(file_path2, 'w', newline='') as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow(header)
            writer.writerows(data_rows) 

        with open(file_path2, 'rb') as file:
            file_content = file.read()

        frappe.db.set_value("Bank Account", doc_name, "custom_beneficiary_file_uploaded", 1)
        frappe.db.commit()
        
        print(f'File {file_name} created successfully in {directory}.')
        return f"File created successfully: {file_name}"

    except Exception as e :
        frappe.log_error(message=str(e), title="Beneficiary File Creation Error")
        return str(e)


@frappe.whitelist()
# Upload Modified Approved Beneficiary file on Snorkel with Indicator M
def upload_beneficiary_file_for_modified_doc(doc_name):
    try:

        numeric_characters = string.digits
        unique_batch_number = ''.join(random.choices(numeric_characters, k=6))

        current_date = datetime.now()
        formatted_date = current_date.strftime("%d%m%Y")

        file_name = f"MANTRASH2H_MANTRABENH2HUP_{formatted_date}_{unique_batch_number}.txt"

        directory_sql = """
            SELECT beneficiary_file_upload_path
            FROM `tabBank Integration`
            WHERE upload_beneficiary_file = 1
        """

        directory_list = frappe.db.sql(directory_sql, as_dict=True) 

        # directory_list = frappe.db.get_list("Bank Integration", filters={'upload_beneficiary_file':1}, fields=["beneficiary_file_upload_path"])

        if not directory_list:
            frappe.throw("Upload beneficiary file path not set in 'Bank Integration'")

        directory = directory_list[0].get("beneficiary_file_upload_path")

        if not directory:
            frappe.throw("Upload beneficiary file path not set in 'Bank Integration'")

        # file_path = os.path.join(directory, file_name)
        file_path = os.path.join('/home/mantra/ICICI_Bank_integration/epayments/beneupload', file_name)
        file_path2 = os.path.join('/home/mantra/Desktop', file_name)

        header = [
                'Indicator','Beneficiary Code','Beneficiary Name','Beneficiary IFSC','Beneficiary Account No','Beneficiary Address'
            ]

        bank_account = frappe.get_doc("Bank Account", doc_name)

        data_rows = [[
            "M",  # Indicator
            bank_account.party,  # Beneficiary Code
            bank_account.account_name,  # Beneficiary Name
            bank_account.custom_ifsc,  # Beneficiary IFSC
            bank_account.bank_account_no,  # Beneficiary Account No
            bank_account.custom_branch_location  # Beneficiary Address
        ]]

        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow(header)
            writer.writerows(data_rows) 

        with open(file_path, 'rb') as file:
            file_content = file.read()

        with open(file_path2, 'w', newline='') as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow(header)
            writer.writerows(data_rows) 

        with open(file_path2, 'rb') as file:
            file_content = file.read()

        frappe.db.set_value("Bank Account", doc_name, "custom_beneficiary_file_uploaded", 1)
        frappe.db.commit()
        
        print(f'File {file_name} created successfully in {directory}.')
        return f"File created successfully: {file_name}"

    except Exception as e :
        frappe.log_error(message=str(e), title="Beneficiary File Creation Error")
        return str(e)


@frappe.whitelist()
# Upload Approved Beneficiary file on Snorkel with Indicator D
def upload_beneficiary_file_for_cancelled_doc(doc_name):
    try:

        numeric_characters = string.digits
        unique_batch_number = ''.join(random.choices(numeric_characters, k=6))

        current_date = datetime.now()
        formatted_date = current_date.strftime("%d%m%Y")

        file_name = f"MANTRASH2H_MANTRABENH2HUP_{formatted_date}_{unique_batch_number}.txt"

        directory_sql = """
            SELECT beneficiary_file_upload_path
            FROM `tabBank Integration`
            WHERE upload_beneficiary_file = 1
        """

        directory_list = frappe.db.sql(directory_sql, as_dict=True) 
        # directory_list = frappe.db.get_list("Bank Integration", filters={'upload_beneficiary_file':1}, fields=["beneficiary_file_upload_path"])

        if not directory_list:
            frappe.throw("Upload beneficiary file path not set in 'Bank Integration'")

        directory = directory_list[0].get("beneficiary_file_upload_path")

        if not directory:
            frappe.throw("Upload beneficiary file path not set in 'Bank Integration'")

        file_path = os.path.join('/home/mantra/ICICI_Bank_integration/epayments/beneupload', file_name)
        file_path2 = os.path.join('/home/mantra/Desktop', file_name)

        header = [
                'Indicator','Beneficiary Code','Beneficiary Name','Beneficiary IFSC','Beneficiary Account No','Beneficiary Address'
            ]

        bank_account = frappe.get_doc("Bank Account", doc_name)

        data_rows = [[
            "D",  # Indicator
            bank_account.party,  # Beneficiary Code
            bank_account.account_name,  # Beneficiary Name
            bank_account.custom_ifsc,  # Beneficiary IFSC
            bank_account.bank_account_no,  # Beneficiary Account No
            bank_account.custom_branch_location  # Beneficiary Address
        ]]

        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow(header)
            writer.writerows(data_rows) 

        with open(file_path, 'rb') as file:
            file_content = file.read()

        

        with open(file_path2, 'w', newline='') as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow(header)
            writer.writerows(data_rows) 

        with open(file_path2, 'rb') as file:
            file_content = file.read()

        frappe.db.set_value("Bank Account", doc_name, "custom_beneficiary_file_uploaded", 1)
        frappe.db.commit()
        
        # print(f'File {file_name} created successfully in {directory}.')
        return f"File created successfully: {file_name}"

    except Exception as e :
        frappe.log_error(message=str(e), title="Beneficiary File Creation Error")
        return str(e)


@frappe.whitelist()
# get reverse MIS of Beneficiary File
def get_bene_file(delimiter='|'):
    try:
        folder_path = '/home/mantra/ICICI_Bank_integration/epayments/PayReportBackup'
        one_hour_ago = datetime.now() - timedelta(hours=1)

        processed_files = []
        errors = []

        # Get recipients based on role
        # role = "Upload Bene"  # Replace with the actual role name
        # recipients = frappe.db.sql(
        #     """
        #     SELECT DISTINCT u.email
        #     FROM `tabUser` u
        #     INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        #     WHERE hr.role = %s AND u.enabled = 1 AND u.user_type = 'System User' AND u.email IS NOT NULL
        #     """,
        #     role,
        #     as_dict=True
        # )
        # recipient_emails = [user.email for user in recipients]

        # if not recipient_emails:
        #     frappe.logger().warning("No recipients found for the role.")
        #     return {"status": "error", "message": "No recipients found for the specified role."}

        for file_name in os.listdir(folder_path):
            if file_name.endswith('.txt'):
                csv_file_path = os.path.join(folder_path, file_name)
                modification_time = datetime.fromtimestamp(os.path.getmtime(csv_file_path))

                if modification_time >= one_hour_ago:
                    frappe.logger().info(f"Processing file: {file_name} (Modified at {modification_time})")
                    processed_files.append(file_name)

                    data = []
                    with open(csv_file_path, mode='r') as file:
                        for line in file:
                            row = line.strip().split(delimiter)
                            if len(row) < 8:
                                frappe.logger().warning(f"Skipping row with insufficient columns: {row}")
                                continue
                            data.append(row)

                    for data_dict in data:
                        try:
                            if data_dict[0] == "P" and data_dict[6] == "Added":
                                bank_account_no = data_dict[4]
                                bank_account_doc = frappe.db.get_value(
                                    "Bank Account", 
                                    {"bank_account_no": bank_account_no, "docstatus": 1}, 
                                    "name"
                                )
                                if bank_account_doc:
                                    frappe.db.set_value(
                                        "Bank Account", bank_account_doc, {"custom_remark": data_dict[7]}
                                    )
                                    frappe.db.commit()

                            elif data_dict[0].startswith("MANTRASH2H_MANTRABENH2HUP"):
                                bank_account_no = data_dict[5]
                                bank_account_doc = frappe.db.get_value(
                                    "Bank Account", 
                                    {"bank_account_no": bank_account_no, "docstatus": 1}, 
                                    "name"
                                )
                                if bank_account_doc:
                                    frappe.db.set_value(
                                        "Bank Account", bank_account_doc, {
                                            "workflow_state": "Rejected",
                                            "custom_beneficiary_file_uploaded": 0,
                                            "custom_remark": data_dict[8]
                                        }
                                    )
                                    # frappe.db.commit()
                                    error_message = f"""
                                        <p><strong>File:</strong> {file_name}</p>
                                        <p><strong>Row Data:</strong> {data_dict}</p>
                                        <p>The workflow state has been set to "Rejected" for the bank account with account number: {bank_account_no}.</p>
                                    """
                                    send_bene_file_error_email(error_message)
                                

                        except Exception as e:
                            frappe.logger().error(f"Error processing row {data_dict}: {e}")
                            errors.append({"file": file_name, "row": data_dict, "error": str(e)})

        if errors:
            error_details = "".join([
                f"""
                <p><strong>File:</strong> {error['file']}</p>
                <p><strong>Row:</strong> {error['row']}</p>
                <p><strong>Error:</strong> {error['error']}</p>
                <hr>
                """ for error in errors
            ])
            send_bene_file_error_email(error_details)

    except FileNotFoundError as e:
        error_message = f"Folder path {folder_path} not found. Exception: {str(e)}"
        send_bene_file_error_email(error_message)

    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        send_bene_file_error_email(error_message)

def send_bene_file_error_email(error_message):
    """
    Sends an email with the error message.
    """
    recipients = ["mailto:ravi.patel@mantratec.com","helpdesk.erp"]  # Replace with actual recipients
    subject = "Error in Beneficiary File Processing"
    message = f"""
    <p>Dear User,</p>
    <p>An error occurred during the execution of the scheduled task:</p>
    <p>{error_message}</p>
    <p>Please check the logs and take necessary action.</p>
    """
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message
        )
        send = flush()
        print(f"Error email sent to: {recipients}")
        frappe.logger().info(f"Error email sent to: {recipients}")
    except Exception as email_error:
        print(f"Failed to send error email: {email_error}")
        frappe.logger().error(f"Failed to send error email: {email_error}")



# @frappe.whitelist()
# # get reverse MIS of Beneficiary File
# def get_bene_file(delimiter='|'):
#     try:
#         folder_path = '/home/mantra/ICICI_Bank_integration/epayments/PayReportBackup'
#         one_hour_ago = datetime.now() - timedelta(hours=1)

#         processed_files = []
#         errors = []

#         # Get recipients based on role
#         # role = "Upload Bene"  # Replace with the actual role name
#         # recipients = frappe.db.sql(
#         #     """
#         #     SELECT DISTINCT u.email
#         #     FROM `tabUser` u
#         #     INNER JOIN `tabHas Role` hr ON hr.parent = u.name
#         #     WHERE hr.role = %s AND u.enabled = 1 AND u.user_type = 'System User' AND u.email IS NOT NULL
#         #     """,
#         #     role,
#         #     as_dict=True
#         # )
#         # recipient_emails = [user.email for user in recipients]

#         # if not recipient_emails:
#         #     frappe.logger().warning("No recipients found for the role.")
#         #     return {"status": "error", "message": "No recipients found for the specified role."}

#         for file_name in os.listdir(folder_path):
#             if file_name.endswith('.txt'):
#                 csv_file_path = os.path.join(folder_path, file_name)
#                 modification_time = datetime.fromtimestamp(os.path.getmtime(csv_file_path))

#                 if modification_time >= one_hour_ago:
#                     frappe.logger().info(f"Processing file: {file_name} (Modified at {modification_time})")
#                     processed_files.append(file_name)

#                     data = []
#                     with open(csv_file_path, mode='r') as file:
#                         for line in file:
#                             row = line.strip().split(delimiter)
#                             if len(row) < 8:
#                                 frappe.logger().warning(f"Skipping row with insufficient columns: {row}")
#                                 continue
#                             data.append(row)

#                     for data_dict in data:
#                         try:
#                             if data_dict[0] == "P" and data_dict[6] == "Added":
#                                 bank_account_no = data_dict[4]
#                                 bank_account_doc = frappe.db.get_value(
#                                     "Bank Account", 
#                                     {"bank_account_no": bank_account_no, "docstatus": 1}, 
#                                     "name"
#                                 )
#                                 if bank_account_doc:
#                                     frappe.db.set_value(
#                                         "Bank Account", bank_account_doc, {"custom_remark": data_dict[7]}
#                                     )
#                                     frappe.db.commit()

#                             elif data_dict[0].startswith("MANTRASH2H_MANTRABENH2HUP"):
#                                 bank_account_no = data_dict[5]
#                                 bank_account_doc = frappe.db.get_value(
#                                     "Bank Account", 
#                                     {"bank_account_no": bank_account_no, "docstatus": 1}, 
#                                     "name"
#                                 )
#                                 if bank_account_doc:
#                                     frappe.db.set_value(
#                                         "Bank Account", bank_account_doc, {
#                                             "workflow_state": "Rejected",
#                                             "custom_beneficiary_file_uploaded": 0,
#                                             "custom_remark": data_dict[8]
#                                         }
#                                     )
#                                     frappe.db.commit()

#                                     # frappe.sendmail(
#                                     #     recipients=recipient_emails,
#                                     #     subject="Beneficiary File Processing Alert",
#                                     #     message=f"""
#                                     #         <p><strong>File:</strong> {file_name}</p>
#                                     #         <p><strong>Row Data:</strong> {data_dict}</p>
#                                     #         <p>The workflow state has been set to "Rejected" for the bank account with account number: {bank_account_no}.</p>
#                                     #     """
#                                     # )
#                                     # send = flush()

#                         except Exception as e:
#                             frappe.logger().error(f"Error processing row {data_dict}: {e}")
#                             errors.append({"file": file_name, "row": data_dict, "error": str(e)})

#         if errors:
#             error_details = "".join([
#                 f"""
#                 <p><strong>File:</strong> {error['file']}</p>
#                 <p><strong>Row:</strong> {error['row']}</p>
#                 <p><strong>Error:</strong> {error['error']}</p>
#                 <hr>
#                 """ for error in errors
#             ])
#             # frappe.sendmail(
#             #     recipients=recipient_emails,
#             #     subject="Errors in Beneficiary File Processing",
#             #     message=f"""
#             #         <p>The following errors occurred while processing the beneficiary files:</p>
#             #         {error_details}
#             #     """
#             # )
#             # send = flush()
#         return {"status": "success", "files_processed": processed_files, "errors": errors}

#     except FileNotFoundError as e:
#         error_message = f"Folder path {folder_path} not found. Exception: {str(e)}"
#         frappe.logger().error(error_message)
#         # frappe.sendmail(
#         #     recipients=recipient_emails,
#         #     subject="Beneficiary File Processing - Exception Occurred",
#         #     message=f"""
#         #         <p><strong>Exception:</strong> {error_message}</p>
#         #     """
#         # )
#         # send = flush()
#         return {"status": "error", "message": error_message}

#     except Exception as e:
#         error_message = f"Unexpected error: {str(e)}"
#         frappe.logger().error(error_message)
#         # frappe.sendmail(
#         #     recipients=recipient_emails,
#         #     subject="Beneficiary File Processing - Exception Occurred",
#         #     message=f"""
#         #         <p><strong>Exception:</strong> {error_message}</p>
#         #     """
#         # )
#         # send = flush()
#         return {"status": "error", "message": error_message}

# Check User & then end Otp On Email
@frappe.whitelist(allow_guest=True)
def send_otp(email):
    # frappe.msgprint(email)
    filters = {
        "name": email,
        "enabled":1
    }
    #check user are exists or not
    userexists = frappe.db.exists("User", filters)
    print(userexists,"\n\n\n\n\n\n")
    # If record exists, return True
    if userexists:
        otpsend = frappe.db.exists("Email OTP", {"email_id":email})
        numeric_characters = string.digits
        alphabet_characters = string.ascii_letters
    
        # Generate the OTP with 2 numeric characters and 1 alphabetical character
        otp1 = ''.join(random.choices(numeric_characters, k=2)) + random.choice(alphabet_characters)
        otp2 = random.choice(numeric_characters) + ''.join(random.choices(alphabet_characters, k=2))

        
        email_otp=otp1+otp2
        if otpsend:
            # Update Send otp Log
            new_otp=frappe.get_doc("Email OTP",email)
            new_otp.email_otp=email_otp
            new_otp.datetime=now()
            new_otp.save(ignore_permissions=True)
            frappe.db.commit()
            full_name=new_otp.full_name
            send_email(email,email_otp,full_name)
        else:
            # Create Send otp Log
            # frappe.msgprint("new login")
            new_otp=frappe.new_doc("Email OTP")
            new_otp.email_id=email
            new_otp.email_otp=email_otp
            new_otp.datetime=now()
            new_otp.insert(ignore_permissions=True)
            frappe.db.commit()
            full_name=new_otp.full_name
            send_email(email,email_otp,full_name)
        flush()
        return "Done"
    else:
        frappe.msgprint("User with email {} does not exist".format(email))
        return "Error"
 # this function for a email formate  

def send_email(email,email_otp,full_name):
    frappe.sendmail(
        recipients=email,
        subject="OTP Verification for Payments",
        message=f"""
        <html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
<div style="padding: 1%;background-color: #f4f5f6">
    <div class="box" style="  background-color: #fff;
        padding: 25px;
        border-radius:15px;        
        width: 60%;
        align-items: center;
        margin-top: 100px;
        margin-bottom: 100px;
        margin-left: auto;
        margin-right: auto;">
        <h2>Dear {full_name},</h2>
        <p>Please use the verification code below to complete the Payment Entry Transactions.</p>
        <p>Payment Entry Attempted at {now()}</p>
        <h1>{email_otp}</h1>
        <h4>OTP will expire in 10 minutes.</h4>
        <p>Thank You</p>
        <img src="https://mantratec.milaap.ai/files/Mantra-Logo_1.png">
    </div>
    </div>
</body>
</html>""" 
    )
    send = flush()
    
@frappe.whitelist(allow_guest=True)
#yhis function for verify a otp
def verify_otp(email,otp):
    r_send = frappe.get_doc("Email OTP",email)	
    check_otp = r_send.email_otp
    check_time = r_send.datetime
    date_format = "%Y-%m-%d %H:%M:%S.%f"
    #change Date formate
    ck_time = datetime.strptime(str(check_time) , date_format)
    end_date = now()

    dt_object = datetime.strptime(end_date , date_format)
    start_date = dt_object - timedelta(hours=0, minutes=10)
    #check Otp
    if start_date < ck_time:
        print("if")
        if check_otp==otp:
            #enquiry(mobile,equipment_id)
            # user=email
            return "Done"
        else:
            return "Error"
    else:
        return "Expired"
	

@frappe.whitelist(allow_guest=True)
# this function for ligin
def login_user(user):
    # frappe.msgprint("Test login_user")
    number = frappe.db.get_value("User", user, ['phone'])
    frappe.local.login_manager.user = user
    frappe.local.login_manager.post_login()
    frappe.db.commit()
    
    user_name = frappe.db.sql("select first_name from `tabUser` where name=%s ",user)
    
    user = frappe.session.user
    subject = user_name[0][0]+" logged in"

    if number:
        add_authentication_log(subject,user)
        
    
    

    login_token = frappe.generate_hash(length=32)
    frappe.cache().set_value(
        f"login_token:{login_token}", frappe.local.session.sid, expires_in_sec=120
    )
    
   
    # print("\n\n login token", login_token, "\n\n")
    # return login_token
    return login_via_token(login_token, number,user)

#login with otp
@frappe.whitelist(allow_guest=True)
def login_via_token(login_token: str, number,user):
    sid = frappe.cache().get_value(f"login_token:{login_token}", expires=True)
    if not sid:
        frappe.respond_as_web_page(_("Invalid Request"), _(
            "Invalid Login Token"), http_status_code=417)
        return

    frappe.local.form_dict.sid = sid
   
    frappe.local.login_manager = LoginManager()
    
    return True


@frappe.whitelist()
def get_opration_approver(department):
    doc=frappe.get_doc("Department",department)
    dep_approver=[]
    if doc.custom_opration_approver:
        for i in doc.custom_opration_approver:
            app=frappe.get_doc("Department Approver",i)
            dep_approver.append(app.approver)
    return dep_approver
    
@frappe.whitelist()
def encoded_code():
    # Generate a key for encryption and decryption
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)

    # Generate a 6-digit OTP
    numeric_characters = string.digits
    otp1 = ''.join(random.choices(numeric_characters, k=6))

    # Encrypt the OTP
    encrypted_otp = cipher_suite.encrypt(otp1.encode())

    # Store the encrypted OTP and key in the single document
    doc1 = frappe.get_single("Bank Authentication")
    doc1.encrypted_otp = encrypted_otp.decode()  # Store as string
    doc1.required_key = key.decode()  # Store as string
    doc1.save()
    frappe.db.commit()

    # Decrypt the OTP (for demonstration purposes)
    # decrypted_message = cipher_suite.decrypt(encrypted_otp).decode()
    print(otp1)
    # Print results (for debugging purposes)
   

    return encrypted_otp.decode()
#this function find out payment entry which is ready to push in icici portal
@frappe.whitelist()
def select_payment_entry(bank_account):
    # frappe.msgprint(bank_account)
    # Retrieve the encrypted OTP and key from the single document
    doc1 = frappe.get_single("Bank Authentication")
    # encrypted_otp = doc1.encrypted_otp.encode()  # Convert back to bytes
    # key = doc1.required_key.encode()  # Convert back to bytes

    # Reconstruct the Fernet object from the key
    # cipher_suite = Fernet(key)
    
    # Decrypt the OTP
    # decrypted_message = cipher_suite.decrypt(encrypted_otp).decode()
    
    mdf=frappe.db.sql("select mode_of_payment,abbrivation from `tabMode of Payment Setting` where parent=%s",bank_account,as_dict=True)
    mode_of_payment=[]
    for i in mdf:
        mode_of_payment.append(i["mode_of_payment"])
    # Verify the OTP
    # if decrypted_message == otp:
        # get payment reqest id
    sql_query = """
        SELECT name
        FROM `tabPayment Entry`
        WHERE custom_unique_batch_number IS NULL
        AND docstatus=1
        AND payment_type='Pay'
        AND bank_account=%s
        AND mode_of_payment IN %s
    """
    
    # Execute the query and fetch results as dictionaries
    payment_entry = frappe.db.sql(sql_query, (bank_account, tuple(mode_of_payment)), as_dict=True)       
    print(payment_entry)
    unique_code=0
    payment_entry_list=[]
    for i in payment_entry:
        payment_entry_list.append(i['name'])
    return {"payment_entry_list":payment_entry_list}
     
@frappe.whitelist()
def upload_file(payment_entry_list,bank_account, delimiter=','):
    try :
        if frappe.db.get_value("Bank Integration", bank_account, "bank")=="ICICI Bank Limited":
           icici_file_create(bank_account,payment_entry_list,delimiter=',')
           return "Done"
           
        elif frappe.db.get_value("Bank Integration", bank_account, "bank")=="Punjab National Bank":
            pnb_file_create(bank_account,payment_entry_list,delimiter=',')  
        else :
            frappe.throw("Worng Bank Selected")          
    except Exception as e:
        print(e)
    
    # print(type(list_items))
    
#this function is use for a push file in icici snorken folder 
def icici_file_create(bank_account, payment_entry_list, delimiter='|'):
    try :
        numeric_characters = string.digits
        directory = frappe.db.get_value("Bank Integration", bank_account, "file_upload_path")
        print(directory)
        
        unique_batch_number = ''.join(random.choices(numeric_characters, k=6))
        list_items = ast.literal_eval(payment_entry_list)
        
        # file_name = f"MANTRAS_MANTRASDNLD_{unique_batch_number}.txt"
        current_date = datetime.now()
        formatted_date = current_date.strftime("%d%m%Y")
        file_name = f"MANTRASH2H_MANTRASH2HUP_{formatted_date}_{unique_batch_number}.txt"
        file_path = os.path.join(directory, file_name)
        # file_path2 = os.path.join('/home/mantra/Desktop/Payments', file_name)
        print("\n\n",file_path,"\n\n")
        total_amount = 0
        
        header = [
            'Debit Ac No', 'beneficiary code', 'Beneficiary Ac No', 'Beneficiary Name',
            'Amt', 'Pay Mod', 'Date', 'IFSC', 'Payable Location name', 'Print Location',
            'Bene Mobile no', 'Bene email id', 'Ben add1', 'Ben add2', 'Ben add3',
            'Ben add4', 'Add details 1', 'Add details 2', 'Add details 3',
            'Add details 4', 'Add details 5', 'Remarks'
        ]
        
        data_rows = []
        email_data= []
        sr_no=0
        for i in list_items:
            payment_entry = frappe.get_doc("Payment Entry", i)
            mdf = frappe.db.sql("""
                SELECT mode_of_payment, abbrivation 
                FROM `tabMode of Payment Setting` 
                WHERE parent=%s AND mode_of_payment=%s
            """, (bank_account, payment_entry.mode_of_payment), as_dict=True)
            
            frappe.db.set_value("Payment Entry", payment_entry.name, "custom_unique_batch_number", unique_batch_number)
            
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
            
            frappe.db.set_value("Payment Entry", i, "custom_unique_batch_number", unique_batch_number)
            frappe.db.set_value("Payment Entry", i, "custom_payment_status_", "Processed")
            frappe.db.commit()
            print(f'Data added to {file_path} successfully.')
            entry_type=frappe.db.get_value("Payment Request",payment_entry.reference_no,"custom_payment_type")
            approval_type=frappe.db.get_value("Payment Request",payment_entry.reference_no,"custom_approval_type")
            maker=frappe.db.get_value("Payment Request",payment_entry.reference_no,"owner")
            email_row=[sr_no+1,beneficiary_code,beneficiary_name,amt,entry_type,"",approval_type,"",remarks,maker,bane_add3]
            email_data.append(email_row)

        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow(header)
            writer.writerows(data_rows)
        # with open(file_path2, 'w', newline='') as file:
        #     writer = csv.writer(file, delimiter="|")
        #     writer.writerow(header)
        #     writer.writerows(data_rows)
        email_file_path='/home/mantra/Documents/email_file_folder/ICICI'
        email_file_name=f"MANTRAS_{unique_batch_number}.csv"
        email_path=os.path.join(email_file_path, email_file_name)
        email_header=["Sr.No","Code",'Beneficiary','Amount',' Type','Approval','Approval type','Tally Entry','Remarks','Maker','Checker ']
        with open(email_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(email_header)
            writer.writerows(email_data)


        with open(file_path, 'rb') as file:
            file_content = file.read()
        # with open(file_path2, 'rb') as file:
        #     file_content = file.read()

        with open(email_path, 'rb') as file:
            email_file_content = file.read()
            
        attachments = [{
            'fname': file_name,
            'fcontent': file_content
        },{
            'fname': email_file_name,
            'fcontent': email_file_content
        }]
        
        recipients = []
        rec = frappe.db.sql('select user from `tabBank User` where parent=%s', bank_account, as_dict=True)
        if rec:
            for i in rec:
                recipients.append(i["user"])
        
        print("Recipients:", recipients)
        
        if not recipients:
            print("No recipients found")
        else:
            try:
                frappe.sendmail(
                    recipients=recipients,
                    subject='ICICI Payment Entry',
                    message=f'''
                        <html>
                        <head>
                            <title>ICICI Payment Entry</title>
                        </head>
                        <body>
                            <p>Hello,</p>
                            <p>Please find attached the payment file sent to ICICI.</p>
                            <p>Below are the details of the transaction:</p>
                            <ul>
                                <li>Total amount: {total_amount}</li>
                                <li>Total number of transactions: {len(list_items)}</li>
                                <li>Unique batch number: {unique_batch_number}</li>
                                <li>Time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                                <li>Current User : {frappe.session.user}</li>
                            </ul>
                            <br><br>
                            <p>Regards,</p>
                            <p>Account Manager</p>
                        </body>
                        </html>
                    ''',
                    attachments=attachments
                )
                send=flush()
                print(f'File {file_name} created and email sent successfully.')
                return file_path
            except Exception as e:
                print(e)
        print(f'File {file_name} created successfully in {directory}.')
        return "Done"
    except Exception as e :
        return e

@frappe.whitelist()
# upload salary slip.txt file on snorkel
def generate_salary_slip(payroll_entry=None):
    try:

        directory_sql = """
            SELECT file_upload_path
            FROM `tabBank Integration`
        """

        directory_list = frappe.db.sql(directory_sql, as_dict=True) 

        if not directory_list:
            frappe.throw("Payment File Upload Path not set in 'Bank Integration'")

        directory = directory_list[0].get("file_upload_path")

        if not directory:
            frappe.throw("Payment File Upload Path not set in 'Bank Integration'")

        numeric_characters = string.digits
        unique_batch_number = ''.join(random.choices(numeric_characters, k=6))
        current_date = datetime.now()
        formatted_date = current_date.strftime("%d%m%Y")
        file_name = f"MANTRASH2H_MANTRASH2HUP_{formatted_date}_{unique_batch_number}.txt"

        # file_name = "MANTRASH2H_MANTRASH2HUP.txt"
        # directory = '/home/foramshah/Downloads/epayments/PayUpload'
        # /home/mantra/ICICI_Bank_integration/epayments/PayUpload
        file_path = os.path.join(directory, file_name)

        # Fetch Salary Slip details based on Payroll Entry
        salary_slips = frappe.get_all(
            "Salary Slip",
            filters={"payroll_entry": payroll_entry} if payroll_entry else {},
            fields=["employee", "employee_name", "net_pay", "bank_name", "bank_account_no", "posting_date", "name"]
        )
        
        if not salary_slips:
            frappe.throw("No Salary Slips found for the given Payroll Entry.")

        headers = [
            'Debit Ac No', 'beneficiary code', 'Beneficiary Ac No', 'Beneficiary Name',
            'Amt', 'Pay Mod', 'Date', 'IFSC', 'Payable Location name', 'Print Location',
            'Bene Mobile no', 'Bene email id', 'Ben add1', 'Ben add2', 'Ben add3',
            'Ben add4', 'Add details 1', 'Add details 2', 'Add details 3',
            'Add details 4', 'Add details 5', 'Remarks'
        ]

        rows = []
        for slip in salary_slips:
            payment_account = frappe.db.get_value("Payroll Entry", payroll_entry, "payment_account") or ""
            debit_ac_no = frappe.db.get_value("Account", payment_account, "account_number") or ""
            ifsc_code = frappe.db.get_value("Employee", slip["employee"], "ifsc_code") or ""
            date = datetime.today().strftime('%d-%b-%Y')

            rows.append([
                debit_ac_no,
                slip["employee"],
                slip["bank_account_no"],
                slip["employee_name"],
                slip["net_pay"],
                "",
                date,
                ifsc_code,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                slip["name"],
                "",
                "",
                "",
                "",
                ""
            ])

        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow(headers) 
            writer.writerows(rows)  

        with open(file_path, 'rb') as file:
            file_content = file.read()

        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "file_size": len(file_content),
            "attached_to_doctype": "Payroll Entry",
            "attached_to_name": payroll_entry,
            "content": file_content,
            "is_private": True  # Set this to True if you want it to be private
        })
        file_doc.save()

        print(f'File {file_name} created successfully in {directory}.')
        return f"File created successfully: {file_name}"

    except Exception as e:
        frappe.log_error(message=str(e), title="Salary Slip TXT Generation Error")
        return str(e)

#this function is use for a pnb file creation
def pnb_file_create(bank_account, payment_entry_list, delimiter=','):
    try:
        header = ["Payment Method", "Transaction Reference No.", "Value Date", "Debit A/C no", "Debit A/c Currency", "Beneficiary A/c no", "Beneficiary Code", "Bene Name", "Amount Payable", "Beneficiary Bank BIC Code", "Print Branch", "Transaction Status", "Verified By", "UTR No"]

        # Define the directory and file name
        numeric_characters = string.digits
        directory = frappe.db.get_value("Bank Integration", bank_account, "file_upload_path")
        print(directory)
        unique_batch_number = ''.join(random.choices(numeric_characters, k=6))
        list_items = eval(payment_entry_list)  # Be cautious with eval; prefer using json.loads if possible
        file_name = "MANTRAS_MANTRASDNLD_" + str(unique_batch_number) + ".csv"
        
        os.makedirs(directory, exist_ok=True)
        
        # Construct the file path
        file_path = os.path.join(directory, file_name)
        
        # Create the CSV file and write the header
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(header)
        email_data=[] 
        sr_no = 0
        data_rows = []
        total_amount = 0
        print(list_items)
        for i in list_items:
            payment_entry = frappe.get_doc("Payment Entry", i)
            mdf = frappe.db.sql("SELECT mode_of_payment, abbrivation FROM `tabMode of Payment Setting` WHERE parent=%s AND mode_of_payment=%s", (bank_account, payment_entry.mode_of_payment), as_dict=True)
            pay_mod = mdf[0]["abbrivation"]
            date = payment_entry.posting_date.strftime('%Y-%m-%d')
            debit_ac_no = frappe.db.get_value("Bank Account", payment_entry.bank_account, "bank_account_no") or ""
            beneficiary_ac_no = frappe.db.get_value("Bank Account", payment_entry.party_bank_account, "bank_account_no") or ""
            beneficiary_code = payment_entry.party or ""
            beneficiary_name = payment_entry.party_name or ""
            amt = payment_entry.base_paid_amount_after_tax
            ifsc = frappe.db.get_value("Bank Account", payment_entry.party_bank_account, "custom_ifsc") or ""
            verified_by = payment_entry.custom_approved_by
            new_row = [pay_mod, i, date, debit_ac_no, "INR", beneficiary_ac_no, beneficiary_code, beneficiary_name, amt, ifsc, "CMS HUB", "Processed", verified_by, ""]
            data_rows.append(new_row)
            frappe.db.set_value("Payment Entry", i, "custom_unique_batch_number", unique_batch_number)
            frappe.db.set_value("Payment Entry", i, "custom_payment_status_", "Processed")
            frappe.db.commit()
            bane_add3 = payment_entry.custom_approved_by
            remarks=payment_entry.remarks.replace('\n', ' ') if payment_entry.remarks else ""
            total_amount += amt
            entry_type=frappe.db.get_value("Payment Request",payment_entry.reference_no,"custom_payment_type")
            approval_type=frappe.db.get_value("Payment Request",payment_entry.reference_no,"custom_approval_type")
            maker=frappe.db.get_value("Payment Request",payment_entry.reference_no,"owner")
            email_row=[sr_no+1,beneficiary_code,beneficiary_name,amt,entry_type,"",approval_type,"",remarks,maker,bane_add3]
            email_data.append(email_row)
        
        print(data_rows)
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerows(data_rows)
        email_file_path='/home/mantra/Documents/email_file_folder/ICICI'
        email_file_name=f"MANTRAS_{unique_batch_number}.csv"
        email_path=os.path.join(email_file_path, email_file_name)
        email_header=["Sr.No","Code",'Beneficiary','Amount',' Type','Approval','Approval type','Tally Entry','Remarks','Maker','Checker ']
        with open(email_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(email_header)
            writer.writerows(email_data)    
        print(f'Data added to {file_path} successfully.')
        with open(file_path, 'rb') as file:
            file_content = file.read()
        with open(email_path, 'rb') as file:
            email_file_content = file.read()    
        # Create the attachment
        attachments = [{
            'fname': file_name,
            'fcontent': file_content
        },{
            'fname': email_file_name,
            'fcontent': email_file_content
        }]
        recipients = []
        rec = frappe.db.sql('select user from `tabBank User` where parent=%s', bank_account, as_dict=True)

        if rec:
            for i in rec:
                recipients.append(i["user"])

        # Debug: Print the recipients list
        print("Recipients:", recipients)

        if not recipients:
            print("No recipients found")
        else:
            # Send the email
            try:
                frappe.sendmail(
                    recipients=recipients,
                    subject='PNB Payment Entry',
                    message=f'''
                        <html>
                        <head>
                            <title>PNB Payment Entry</title>
                        </head>
                        <body>
                            <p>Hello,</p>
                            <p>Please find attached the payment file sent to PNB.</p>
                            <p>Below are the details of the transaction:</p>
                            <ul>
                                <li>Total amount: {total_amount}</li>
                                <li>Total number of transactions: {len(list_items)}</li>
                                <li>Unique batch number: {unique_batch_number}</li>
                            </ul>
                            <br><br>
                            <p>Regards,</p>
                            <p>Account Manager</p>
                        </body>
                        </html>
                    ''',
                    attachments=attachments
                )
       

                send=flush()
                return file_path
            except Exception as e :
                print(e)
     
    except Exception as e:
        print("Error sending email:", e)
#get revers Mis From Bank PNB
@frappe.whitelist()
def get_pnb_file():
    # Specify the path to your CSV file
    # folder_path = '/home/mantra/Documents/PNB/recive_file'
    bank_list = frappe.db.get_list("Bank Integration", filters={"bank": "Punjab National Bank"}, fields=["name", "bank", "file_pull_path"])
    print(bank_list)
    all_data = []
    for i in bank_list:
    # Initialize an empty list to store data from all files
        folder_path = i["file_pull_path"]
        print(folder_path)
        

        # Iterate over each file in the specified folder
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.csv'):
                csv_file_path = os.path.join(folder_path, file_name)
                
                # Initialize an empty list to store data from the current file
                data = []
                
                # Open the CSV file and read its contents
                with open(csv_file_path, mode='r') as file:
                    reader = csv.DictReader(file)
                    
                    # Iterate over each row in the CSV
                    for row in reader:
                        data.append(row)
                
                # Convert the list of dictionaries to JSON format
                json_data = json.dumps(data, indent=4)
                
                # Print or use the JSON data as needed
                # print(f'JSON data for file {file_name}:\n{json_data}\n')

                # Append the data to the all_data list
                all_data.extend(data)

        # If you want to use the combined data from all files as JSON
    combined_json_data = json.dumps(all_data, indent=4)
    parsed_data = json.loads(combined_json_data)
    for data_dict in parsed_data:
            print(data_dict,"\n\n\n")
            if data_dict["Transaction Status"]=="Successful":
                    # pay_entry=frappe.get_doc("Payment Entery")
                    frappe.db.set_value("Payment Entry",data_dict["Transaction Reference No."],"custom_payment_status_","Successful")
                    frappe.db.set_value("Payment Entry",data_dict["Transaction Reference No."],"custom_utr_no",data_dict["UTR No"])
                    frappe.db.commit()
            else:
                    frappe.db.set_value("Payment Entry",data_dict["Transaction Reference No."],"custom_payment_status_","Failed")
                    frappe.db.set_value("Payment Entry",data_dict["Transaction Reference No."],"custom_utr_no",data_dict["UTR No"])
                    frappe.db.set_value("Payment Entry",data_dict["Transaction Reference No."],"docstatus",2)
                    frappe.db.commit()
    print(parsed_data)

#get revers Mis From Bank ICICI
@frappe.whitelist()
def get_icici_bank_file(delimiter='|'):   
    try:
        # Get the path to the folder containing the files
        folder_path = frappe.db.get_value("Bank Integration", "Mantra - ICICI Bank Limited - 018951000027", "file_pull_path")
        # Specify the path to the backup folder
        backup_folder = frappe.db.get_value("Bank Integration", "Mantra - ICICI Bank Limited - 018951000027", "file_backup_path")
        
        print("Folder path:", folder_path)
        print("Backup folder:", backup_folder)

        # data = [] 
        # all_data = []
          
        # Iterate over each file in the specified folder
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.txt'):
                csv_file_path = os.path.join(folder_path, file_name)
                
                # Initialize an empty list to store data from the current file
                data = []
                
                # Open the CSV file and read its contents
                with open(csv_file_path, mode='r') as file:
                    for line in file:
                        row = line.strip().split(delimiter)
                        # print(row)
                        data.append(row)
                
                # print(len(data))
                # print("Data are printed")
                
                # i1 = 0
                for data_dict in data:
                    # print("\n\n\n\n", (data_dict,"vnlkjmkjmj"), "\n\n\n\n")
                    # i1 = i1 + 1
                    
                    try:
                        # data_dict1 = {
                        # "Status": data_dict[22],
                        # }
                        # print(data_dict1,"Dictdata 1")
                        # payment_entry_name = data_dict[15]
                        # status = data_dict1["Status"]
                        if frappe.db.exists("Payment Entry", data_dict[15]):
                            print("Payment : ",data_dict[15])

                            ERP_status = ""
                            rejection_reason = ""


                            if data_dict[22] == "Paid" or data_dict[22]=="Authorization Pending" or data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
                                if data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
                                    ERP_status = "Fail"
                                    rejection_reason = "Rejected"

                                    # payment_entry = frappe.get_doc("Payment Entry", data_dict[15])
            
                                    # Cancel the document
                                    # payment_entry.cancel()

                                    frappe.db.set_value("Payment Entry", data_dict[15], {
                                    "workflow_state": "Cancelled",
                                    })
                                    
                                else:
                                    if data_dict[22] == "Paid":
                                        ERP_status = "Success"
                                    else:
                                        ERP_status = "Authorization Pending"
                                    
                                frappe.db.set_value("Payment Entry", data_dict[15], {
                                    "custom_payment_status_": ERP_status,
                                    "custom_payment_ref_no": data_dict[21],
                                    "custom_customer_ref_no": data_dict[24],
                                    "custom_instrument_no": data_dict[26],
                                    "custom_instrument_ref_no": data_dict[25],
                                    "custom_liquidation_date": data_dict[23],
                                    "custom_utr_no":  data_dict[28],
                                    "custom_rejection_reason":rejection_reason,
                                    # "docstatus": docstatus
                                })
                                # frappe.db.commit()



                        
                            # if data_dict[22] == "Paid" or data_dict[22]=="Authorization Pending" or data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
                                # if data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
                                    # docstatus = 2
                                #     frappe.db.set_value("Payment Entry", data_dict[15], {
                                #     "custom_payment_status_": ERP_status,
                                #     "custom_payment_ref_no": data_dict[21],
                                #     "custom_customer_ref_no": data_dict[24],
                                #     "custom_instrument_no": data_dict[26],
                                #     "custom_instrument_ref_no": data_dict[25],
                                #     "custom_liquidation_date": data_dict[23],
                                #     "custom_utr_no":  data_dict[28],
                                #     "custom_rejection_reason":data_dict[22],
                                #     "docstatus": docstatus
                                #     })
                                #     frappe.db.commit()

                                # else :
                                #     payment_status = data_dict[22]
                                #     print(payment_status)
                                #     docstatus = 1
                                #     frappe.db.set_value("Payment Entry", data_dict[15], {
                                #     "custom_payment_status_": ERP_status,
                                #     "custom_payment_ref_no": data_dict[21],
                                #     "custom_customer_ref_no": data_dict[24],
                                #     "custom_instrument_no": data_dict[26],
                                #     "custom_instrument_ref_no": data_dict[25],
                                #     "custom_liquidation_date": data_dict[23],
                                #     "custom_utr_no":  data_dict[28],
                                #     "docstatus": docstatus,
                                    
                                #     })
                                #     frappe.db.commit()

                        elif frappe.db.exists("Salary Slip", data_dict[15]):
                            print("Salary : ",data_dict[15])

                            ERP_status = ""
                            rejection_reason = ""

                            if data_dict[22] == "Paid" or data_dict[22]=="Authorization Pending" or data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
                                if data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
                                    ERP_status = "Fail"
                                    rejection_reason = "Rejected"

                                    # frappe.db.set_value("Payment Entry", data_dict[15], {
                                    # "workflow_state": "Cancelled",
                                    # })

                                else:
                                    if data_dict[22] == "Paid":
                                        ERP_status = "Success"
                                    else:
                                        ERP_status = "Authorization Pending"

                            # Update Salary Slip
                                frappe.db.set_value("Salary Slip", data_dict[15], {
                                    "custom_payment_status": ERP_status,
                                    "custom_payment_ref_no": data_dict[21],
                                    "custom_customer_ref_no": data_dict[24],
                                    "custom_instrument_no": data_dict[26],
                                    "custom_instrument_ref_no": data_dict[25],
                                    "custom_liquidation_date": data_dict[23],
                                    "custom_utr_no":  data_dict[28],
                                    "custom_rejection_reason":rejection_reason,
                                })
                            # frappe.db.commit()

                        else:
                            if frappe.db.exists("Payment Entry", data_dict[17]):
                                print("Payment : ",data_dict[17]) 

                                if data_dict[24]=="P":
                                    frappe.db.set_value("Payment Entry", data_dict[17], {
                                        "custom_rejection_reason":data_dict[25],
                                        "custom_payment_status_": "Fail",
                                        "workflow_state": "Cancelled",
                                    })
                                    # frappe.db.commit()
                                else:
                                    frappe.db.set_value("Payment Entry", data_dict[17], {
                                        "custom_payment_status_": "Fail",
                                        "workflow_state": "Cancelled",
                                    })
                                    # frappe.db.commit()

                            elif frappe.db.exists("Salary Slip", data_dict[17]):
                                print("Salary : ",data_dict[17])

                                if data_dict[24]=="P":
                                    frappe.db.set_value("Salary Slip", data_dict[17], {
                                        "custom_rejection_reason":data_dict[25],
                                        "custom_payment_status": "Fail",
                                    })
                                else:
                                    frappe.db.set_value("Salary Slip", data_dict[17], {
                                        "custom_payment_status": "Fail",
                                    })

                    # except KeyError as ke:
                    #     print(f"KeyError: {ke}")
                        
                    # except Exception as e:
                    #     print(f"An error occurred while updating Payment Entry: {e}")

                    except KeyError as ke:
                        error_message = f"KeyError: {ke} in file {file_name}"
                        send_icici_bank_file_error_email(error_message)

                    except Exception as e:
                        error_message = f"An error occurred while processing data_dict: {e} in file {file_name}"
                        send_icici_bank_file_error_email(error_message)


                backup_file_path = os.path.join(backup_folder, file_name)
                shutil.move(csv_file_path, backup_file_path)
                print(f"File '{file_name}' has been moved to the backup folder.")
                # Move the file to the backup folder after processing
                
        get_bene_result = get_bene_file(delimiter=delimiter)
        print("Beneficiary file processing result:", get_bene_result)     
                
    
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #     return e

    except Exception as e:
        error_message = f"An error occurred in the get_icici_bank_file function: {e}"
        send_icici_bank_file_error_email(error_message)

def send_icici_bank_file_error_email(error_message):
    """
    Sends an email with the error message.
    """
    recipients = ["mailto:ravi.patel@mantratec.com","helpdesk.erp"]  # Replace with actual recipients
    subject = "Error in ICICI Bank File Processing"
    message = f"""
    <p>Dear User,</p>
    <p>An error occurred during the execution of the scheduled task:</p>
    <p>{error_message}</p>
    <p>Please check the logs and take necessary action.</p>
    """
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message
        )
        send = flush()
        print(f"Error email sent to: {recipients}")
    except Exception as email_error:
        print(f"Failed to send error email: {email_error}")
 

# #get revers Mis From Bank ICICI
# @frappe.whitelist()
# def get_icici_bank_file(delimiter='|'):   
#     try:
#         # Get the path to the folder containing the files
#         folder_path = frappe.db.get_value("Bank Integration", "Mantra - ICICI Bank Limited - 018951000027", "file_pull_path")
#         # Specify the path to the backup folder
#         backup_folder = frappe.db.get_value("Bank Integration", "Mantra - ICICI Bank Limited - 018951000027", "file_backup_path")
        
#         print("Folder path:", folder_path)
#         print("Backup folder:", backup_folder)
        
#         data = [] 
#         all_data = []
          
#         # Iterate over each file in the specified folder
#         for file_name in os.listdir(folder_path):
#             if file_name.endswith('.txt'):
#                 csv_file_path = os.path.join(folder_path, file_name)
                
#                 # Initialize an empty list to store data from the current file
#                 data = []
                
#                 # Open the CSV file and read its contents
#                 with open(csv_file_path, mode='r') as file:
#                     for line in file:
#                         row = line.strip().split(delimiter)
#                         print(row)
#                         data.append(row)
                
#                 print(len(data))
#                 print("Data are printed")
                
#                 i1 = 0
#                 for data_dict in data:
#                     print("\n\n\n\n", (data_dict,"vnlkjmkjmj"), "\n\n\n\n")
#                     i1 = i1 + 1
                    
#                     try:
#                         # data_dict1 = {
#                         # "Status": data_dict[22],
#                         # }
#                         # print(data_dict1,"Dictdata 1")
#                         # payment_entry_name = data_dict[15]
#                         # status = data_dict1["Status"]
                        
#                         if data_dict[22] == "Paid" or data_dict[22]=="Authorization Pending" or data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
#                             if data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
#                                 docstatus = 2
#                                 frappe.db.set_value("Payment Entry", data_dict[15], {
#                                 "custom_payment_status_": "Rejected",
#                                 "custom_payment_ref_no": data_dict[21],
#                                 "custom_customer_ref_no": data_dict[24],
#                                 "custom_instrument_no": data_dict[26],
#                                 "custom_instrument_ref_no": data_dict[25],
#                                 "custom_liquidation_date": data_dict[23],
#                                 "custom_utr_no":  data_dict[28],
#                                 "custom_rejection_reason":data_dict[22],
#                                 "docstatus": docstatus
#                                 })
#                                 frappe.db.commit()

#                             else :
#                                 payment_status = data_dict[22]
#                                 docstatus = 1
#                                 frappe.db.set_value("Payment Entry", data_dict[15], {
#                                 "custom_payment_status_": payment_status,
#                                 "custom_payment_ref_no": data_dict[21],
#                                 "custom_customer_ref_no": data_dict[24],
#                                 "custom_instrument_no": data_dict[26],
#                                 "custom_instrument_ref_no": data_dict[25],
#                                 "custom_liquidation_date": data_dict[23],
#                                 "custom_utr_no":  data_dict[28],
#                                 "docstatus": docstatus,
                                
#                                 })
#                                 frappe.db.commit()
#                         else: 
#                                 if data_dict[24]=="P":
#                                     frappe.db.set_value("Payment Entry", data_dict[17], {
#                                     "custom_rejection_reason":data_dict[25],
#                                     "custom_payment_status_": "Fail",
#                                     "docstatus": 2,
                                    
#                                     })
#                                     frappe.db.commit()
#                                 else:
#                                     frappe.db.set_value("Payment Entry", data_dict[17], {
#                                     "custom_payment_status_": "Fail",
#                                     "docstatus": 2,
#                                     })
#                                     frappe.db.commit()

#                     except KeyError as ke:
#                         print(f"KeyError: {ke}")
                        
#                     except Exception as e:
#                         print(f"An error occurred while updating Payment Entry: {e}")
#                 backup_file_path = os.path.join(backup_folder, file_name)
#                 shutil.move(csv_file_path, backup_file_path)
#                 print(f"File '{file_name}' has been moved to the backup folder.")  
#                 # Move the file to the backup folder after processing
                
#         get_bene_result = get_bene_file(delimiter=delimiter)
#         print("Beneficiary file processing result:", get_bene_result)           
                  
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return e

@frappe.whitelist()
def send_frappe_mail():   
    try:
        # Define the email parameters
        # recipients = 'dhruvikaneriya52@gamil.com'
        # subject = 'Subject of the Email'
        # message = 'Body of the email'
        
        # Read the file content
        file_path = '/home/mantra/Documents/PNB/recive_file/MANTRAS_MANTRASDNLD_586483.csv'
        with open(file_path, 'rb') as file:
            file_content = file.read()
        
        # Create the attachment
        attachments = [{
            'fname': 'MANTRAS_MANTRASDNLD_586483.csv',
            'fcontent': file_content
        }]
        
        # Send the email
        frappe.sendmail(
            recipients = 'dhruvikaneriya52@gmail.com',
            subject = 'Subject of the Email',
            message = 'Body of the email',
            attachments=attachments
        )
        send = flush()
    except Exception as e:
        return e
