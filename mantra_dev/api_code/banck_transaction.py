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

        file_path = os.path.join(directory, file_name)

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

        file_path = os.path.join(directory, file_name)

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

        frappe.db.set_value("Bank Account", doc_name, "custom_beneficiary_file_uploaded", 1)
        frappe.db.commit()
        
        # print(f'File {file_name} created successfully in {directory}.')
        return f"File created successfully: {file_name}"

    except Exception as e :
        frappe.log_error(message=str(e), title="Beneficiary File Creation Error")
        return str(e)

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
            date = datetime.strptime(input_date, "%Y-%m-%d").strftime("%d-%b-%Y")
            remarks = payment_entry.remarks.replace('\n', ' ') if payment_entry.remarks else ""
            ifsc = frappe.db.get_value("Bank Account", payment_entry.party_bank_account, "custom_ifsc") or ""
            
            bane_add1 = payment_entry.name
            bane_add2 = payment_entry.owner
            bane_add3 = payment_entry.custom_approved_by
            total_amount += amt
            
            new_row = [
                debit_ac_no, beneficiary_code, beneficiary_ac_no, beneficiary_name,
                amt, pay_mod, date, ifsc, payable_location_name, print_location,
                "Bene Mobile no", "Bene email id", "Ben add1", "Ben add2", "Ben add3",
                "Ben add4", bane_add1, bane_add2, bane_add3, unique_batch_number, "", remarks, ""
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
        
        data = [] 
        all_data = []
          
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
                        print(row)
                        data.append(row)
                
                print(len(data))
                print("Data are printed")
                
                i1 = 0
                for data_dict in data:
                    print("\n\n\n\n", (data_dict,"vnlkjmkjmj"), "\n\n\n\n")
                    i1 = i1 + 1
                    
                    try:
                        # data_dict1 = {
                        # "Status": data_dict[22],
                        # }
                        # print(data_dict1,"Dictdata 1")
                        # payment_entry_name = data_dict[15]
                        # status = data_dict1["Status"]
                        
                        if data_dict[22] == "Paid" or data_dict[22]=="Authorization Pending" or data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
                            if data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
                                docstatus = 2
                                frappe.db.set_value("Payment Entry", data_dict[15], {
                                "custom_payment_status_": "Rejected",
                                "custom_payment_ref_no": data_dict[21],
                                "custom_customer_ref_no": data_dict[24],
                                "custom_instrument_no": data_dict[26],
                                "custom_instrument_ref_no": data_dict[25],
                                "custom_liquidation_date": data_dict[23],
                                "custom_utr_no":  data_dict[28],
                                "custom_rejection_reason":data_dict[22],
                                "docstatus": docstatus
                                })
                                frappe.db.commit()

                            else :
                                payment_status = data_dict[22]
                                docstatus = 1
                                frappe.db.set_value("Payment Entry", data_dict[15], {
                                "custom_payment_status_": payment_status,
                                "custom_payment_ref_no": data_dict[21],
                                "custom_customer_ref_no": data_dict[24],
                                "custom_instrument_no": data_dict[26],
                                "custom_instrument_ref_no": data_dict[25],
                                "custom_liquidation_date": data_dict[23],
                                "custom_utr_no":  data_dict[28],
                                "docstatus": docstatus,
                                
                                })
                                frappe.db.commit()
                        else: 
                                if data_dict[24]=="P":
                                    frappe.db.set_value("Payment Entry", data_dict[17], {
                                    "custom_rejection_reason":data_dict[25],
                                    "custom_payment_status_": "Fail",
                                    "docstatus": 2,
                                    
                                    })
                                    frappe.db.commit()
                                else:
                                    frappe.db.set_value("Payment Entry", data_dict[17], {
                                    "custom_payment_status_": "Fail",
                                    "docstatus": 2,
                                    })
                                    frappe.db.commit()

                    except KeyError as ke:
                        print(f"KeyError: {ke}")
                        
                    except Exception as e:
                        print(f"An error occurred while updating Payment Entry: {e}")
                backup_file_path = os.path.join(backup_folder, file_name)
                shutil.move(csv_file_path, backup_file_path)
                print(f"File '{file_name}' has been moved to the backup folder.")  
                # Move the file to the backup folder after processing
                
                    
                
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return e
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
