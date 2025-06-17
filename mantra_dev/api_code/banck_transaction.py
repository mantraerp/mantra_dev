import frappe # type: ignore
import num2words # type: ignore
import random
import shutil
from frappe.email.email_body import get_pdf # type: ignore
import os
import csv
import json
from frappe.utils import now # type: ignore
from frappe.email.queue import flush # type: ignore
from datetime import datetime, timedelta
from frappe.core.doctype.activity_log.activity_log import add_authentication_log # type: ignore
from frappe.auth import LoginManager # type: ignore
import string
from cryptography.fernet import Fernet # type: ignore
import requests # type: ignore
from datetime import datetime
import traceback
from num2words import num2words # type: ignore
from mantra_dev.backend_code.globle import errorLog,errorLogExites,email_subject_text,send_error_message_to_developer # type: ignore


@frappe.whitelist(allow_guest=True)
def bulk_upload_beneficiary_file2():
	
	#directory_sql = "SELECT name FROM `tabBank Account` WHERE `custom_beneficiary_file_uploaded`=0 AND `workflow_state`='Approved' AND `is_company_account`=0 AND `modified` >= '2025-01-07 00:00:21.876091' LIMIT 200"
	directory_sql = "SELECT name FROM `tabBank Account` WHERE `workflow_state`='Approved' AND `is_company_account`=0 AND `custom_remark` IS NULL LIMIT 200"

	directory_list = frappe.db.sql(directory_sql, as_dict=True)
	# for rrecord in directory_list:
	#     frappe.enqueue(upload_beneficiary_file,queue='long',job_name="Bank approve",timeout=100000,doc_name=rrecord['name'])

		
	return len(directory_list)

@frappe.whitelist(allow_guest=True)
def bulk_upload_beneficiary_file(bank_account_list):
	# errorLog("Bene bulk upload")
	for rrecord in bank_account_list:
		frappe.enqueue(upload_beneficiary_file,queue='long',job_name="Bank approve",timeout=100000,doc_name=rrecord)
	return True

# Upload Approved Beneficiary file on Snorkel with Indicator A
@frappe.whitelist()
def upload_beneficiary_file(doc_name):
	# return
	try:
		numeric_characters = string.digits
		unique_batch_number = ''.join(random.choices(numeric_characters, k=6))

		current_date = datetime.now()
		formatted_date = current_date.strftime("%d%m%Y")

		file_name = f"MANTRASH2H_MANTRABENH2HUP_{formatted_date}_{unique_batch_number}.txt"

		directory_sql = """SELECT beneficiary_file_upload_path FROM `tabBank Integration` WHERE upload_beneficiary_file = 1"""
		directory_list = frappe.db.sql(directory_sql, as_dict=True) 

		if not directory_list:
			frappe.throw("Upload beneficiary file path not set in 'Bank Integration'")

		directory = directory_list[0].get("beneficiary_file_upload_path")

		if not directory:
			frappe.throw("Upload beneficiary file path not set in 'Bank Integration'")

		file_path = os.path.join('/home/mantra/ICICI_Bank_integration/epayments/beneupload', file_name)
		file_path2 = os.path.join('/home/mantra/Desktop/Storing Folder', file_name)

		header = ['Indicator','Beneficiary Code','Beneficiary Name','Beneficiary IFSC','Beneficiary Account No','Beneficiary Address']

		bank_account = frappe.get_doc("Bank Account", doc_name)

		data_rows = [[
			"A",  # Indicator
			bank_account.party.replace("\n", ""),  # Beneficiary Code
			bank_account.account_name.replace("\n", ""),  # Beneficiary Name
			bank_account.custom_ifsc.replace("\n", ""),  # Beneficiary IFSC
			bank_account.bank_account_no.replace("\n", ""),  # Beneficiary Account No
			bank_account.custom_branch_location.replace("\n", "")  # Beneficiary Address
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
		frappe.db.set_value("Bank Account", doc_name, "disabled", 1)
		frappe.db.commit()

		doc = frappe.new_doc('Bank Integration Log')
		doc.file_from = "Mantra"
		doc.file_type = "Bene"
		doc.file_name = file_name
		doc.insert(ignore_permissions=True)


		return f"File created successfully: {file_name}"

	except Exception as e :
		frappe.log_error(message=str(e), title="Beneficiary File Creation Error")
		send_error_message_to_developer("Exception: beneficiary File Creation Error","{}<br>{}".format(str(e),str(traceback.format_exc())))
		return str(e)


# Upload Modified Approved Beneficiary file on Snorkel with Indicator M
@frappe.whitelist()
def upload_beneficiary_file_for_modified_doc(doc_name):
	# return

	try:

		bank_account = frappe.get_doc("Bank Account", doc_name)
		if bank_account.custom_remark in ["Field code Beneficiary Account No does not exists in buyer Mst Table","CMS ERROR  Field code Beneficiary Account No does not exists in buyer Mst Table"]:
			upload_beneficiary_file(doc_name)
			return

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


		data_rows = [[
			"M",  # Indicator
			bank_account.party.replace("\n", ""),  # Beneficiary Code
			bank_account.account_name.replace("\n", ""),  # Beneficiary Name
			bank_account.custom_ifsc.replace("\n", ""),  # Beneficiary IFSC
			bank_account.bank_account_no.replace("\n", ""),  # Beneficiary Account No
			bank_account.custom_branch_location.replace("\n", "")  # Beneficiary Address
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
		frappe.db.set_value("Bank Account", doc_name, "disabled", 1)
		frappe.db.commit()

		doc = frappe.new_doc('Bank Integration Log')
		doc.file_from = "Mantra"
		doc.file_type = "Bene"
		doc.file_name = file_name
		doc.insert(ignore_permissions=True)

		return f"File created successfully: {file_name}"

	except Exception as e :
		frappe.log_error(message=str(e), title="Beneficiary File Creation Error")
		send_error_message_to_developer("Exception: beneficiary File Creation Error","{}<br>{}".format(str(e),str(traceback.format_exc())))
		return str(e)




# Upload Approved Beneficiary file on Snorkel with Indicator D
@frappe.whitelist()
def upload_beneficiary_file_for_cancelled_doc(doc_name):
	# return
	
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
			bank_account.party.replace("\n", ""),  # Beneficiary Code
			bank_account.account_name.replace("\n", ""),  # Beneficiary Name
			bank_account.custom_ifsc.replace("\n", ""),  # Beneficiary IFSC
			bank_account.bank_account_no.replace("\n", ""),  # Beneficiary Account No
			bank_account.custom_branch_location.replace("\n", "")  # Beneficiary Address
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
		frappe.db.set_value("Bank Account", doc_name, "disabled", 1)
		frappe.db.commit()
		


		doc = frappe.new_doc('Bank Integration Log')
		doc.file_from = "Mantra"
		doc.file_type = "Bene"
		doc.file_name = file_name
		doc.insert(ignore_permissions=True)


		return f"File created successfully: {file_name}"

	except Exception as e :
		frappe.log_error(message=str(e), title="Beneficiary File Creation Error")
		send_error_message_to_developer("Exception: beneficiary File Creation Error","{}<br>{}".format(str(e),str(traceback.format_exc())))
		return str(e)


# get reverse MIS of Beneficiary File
@frappe.whitelist()
def get_bene_file(delimiter='|'):
	# return

	try:
		folder_path = '/home/mantra/ICICI_Bank_integration/epayments/PayReportBackup'
		one_hour_ago = datetime.now() - timedelta(hours=1)

		filersreturn = []        
		for file_name in os.listdir(folder_path):
			csv_file_path = os.path.join(folder_path, file_name)
			modification_time = datetime.fromtimestamp(os.path.getmtime(csv_file_path))
			if modification_time >= one_hour_ago:
				if file_name.endswith('.txt'):
					if not errorLogExites('BENYPROCESSFILE',file_name):
						filersreturn.append(file_name)
						errorLog('BENYPROCESSFILE',file_name,True)

		if len(filersreturn)==0:
			return "No files found."


#Start file reading 
		processed_files = []
		errors = []
		data = []
		
		for file_name in filersreturn:
			
			if file_name.startswith("585730452"):
				#Call funcation to send in mefron server
				send_file(csv_file_path,file_name)
			else:
				csv_file_path = os.path.join(folder_path, file_name)
				processed_files.append(file_name)
				
				with open(csv_file_path, mode='r') as file:
					for line in file:
						row = line.strip().split(delimiter)
						if len(row) < 8:
							if not str(row).startswith("['File_Name"):
								if not str(row).startswith("['Indicator'"):
									if not str(row).startswith("['M',"):
										send_error_message_to_developer("Bene file row not suffcient","{}<br>{}".format(str(row),csv_file_path))
						else:
							data.append(row)

		if len(data)==0:
			# frappe.log_error("data","No data found1")
			return "No row found to process"


		for data_dict in data:
			try:
				#If beny get sucussesful uploaded
				if data_dict[0] == "P" and data_dict[6] == "Added":
					bank_account_no = data_dict[4]
					bank_account_doc = frappe.db.get_value(
						"Bank Account", 
						{"bank_account_no": bank_account_no, "docstatus": 1}, 
						"name"
					)
					if bank_account_doc:
						query = "UPDATE `tabBank Account` SET `disabled`=0,`custom_remark`='{}', `custom_beneficiary_file_uploaded`=1 WHERE `name`='{}' AND `docstatus`=1 AND `workflow_state`='Approved'".format(str(data_dict[7])[:100],bank_account_doc)
						mdf = frappe.db.sql(query, as_dict=True)
						# frappe.db.commit()

				elif data_dict[0].startswith("MANTRASH2H_"):

					bank_approve_error = []
					dynamicerror1 = "CMS ERROR Unique combination data does not exists in buyer Mst Table for Buyer code {}".format(str(data_dict[0]))
					bank_approve_error.append(dynamicerror1)
					dynamicerror2 = "CMS ERROR Unique combination data does not exists in buyer Mst Table for Buyer code {}".format(str(data_dict[2]))
					bank_approve_error.append(dynamicerror2)
					dynamicerror3 = "CMS ERROR  Unique combination data does not exists in buyer Mst Table for Buyer code"
					bank_approve_error.append(dynamicerror3)                    
					dynamicerror4 = "CMS ERROR Unique combination data Already exists in buyer Mst Tmp Table"
					bank_approve_error.append(dynamicerror4)                    
					dynamicerror5 = 'Field code Beneficiary Account No Already exists in buyer Mst Tmp Table'
					bank_approve_error.append(dynamicerror5)
					dynamicerror6 = 'CMS ERROR  Field code Beneficiary Account No Already exists in buyer Mst Tmp Table'
					bank_approve_error.append(dynamicerror6)
					dynamicerror7 = 'Unique combination data Already exists in buyer Mst Tmp Table'
					bank_approve_error.append(dynamicerror7)
					
					
					wantToReject = True
					if str(data_dict[8]) in bank_approve_error:
						wantToReject = False
						
					if wantToReject:
						send_error_message_to_developer("Beny rejected","Resone from bank side:{} <br><br><br> Data row: {} <br><br><br> Error list that are handle:{}".format(str(data_dict[8]),str(data_dict),str(bank_approve_error)))


					bank_account_no = data_dict[5]
					bank_account_doc = frappe.db.get_value(
						"Bank Account", 
						{"bank_account_no": bank_account_no, "docstatus": 1}, 
						"name"
					)
					if bank_account_doc:
						if wantToReject:
							frappe.db.set_value(
								"Bank Account", bank_account_doc, {
									"workflow_state": "Rejected",
									"custom_beneficiary_file_uploaded": 0,
									"custom_remark": str(data_dict[8])[:100]
								}
							)
							# frappe.db.commit()
							error_message = f"""
								<p><strong>File:</strong> {file_name}</p>
								<p><strong>Row Data:</strong> {data_dict}</p>
								<p>The workflow state has been set to "Rejected" for the bank account with account number: {bank_account_no}.</p>
							"""
							previous_file = frappe.get_all("Bank Integration Log",filters=[['file_type', '=', 'Mail Send Bene'],['file_name', '=', data_dict[0]]])
							if len(previous_file)==0:
								send_bene_file_error_email(error_message)

								#insert bank transaction log
								doc = frappe.new_doc('Bank Integration Log')
								doc.file_from = "Mantra"
								doc.file_type = "Mail Send Bene"
								doc.file_name = data_dict[0]
								doc.insert(ignore_permissions=True)
						else:

							query = "UPDATE `tabBank Account` SET `disabled`=0,`custom_remark`='{}', `custom_beneficiary_file_uploaded`=1 WHERE `bank_account_no`='{}' AND `docstatus`=1 AND `workflow_state`='Approved'".format(str(data_dict[8])[:100],bank_account_no)
							mdf = frappe.db.sql(query, as_dict=True)
							doc_name = frappe.db.get_value(
								"Bank Account", 
								{"bank_account_no": bank_account_no, "docstatus": 1,"workflow_state":'Approved'}, 
								"name"
							)
							frappe.db.set_value("Bank Account", doc_name, "disabled", 0)


			except Exception as e:
				errors.append({"file": file_name, "row": data_dict, "error": str(e)})

		if errors:
			error_details = "".join([
				f"""
				<p><strong>File:</strong> {error['file']}</p>
				<p><strong>Row:</strong> {error['row']}</p>
				<p><strong>Error:</strong> {error['error']}</p>
				<hr> Test
				""" for error in errors
			])
			send_bene_file_error_email(error_details)

		return "Total process row {}".format(len(data))
	except FileNotFoundError as e:
		error_message = f"Folder path {folder_path} not found. Exception: {str(e)}"
		send_bene_file_error_email(error_message)

	except Exception as e:
		error_message = f"Unexpected error: {str(e)}"
		send_bene_file_error_email(str(traceback.format_exc()))


def send_bene_file_error_email(error_message):
	"""
	Sends an email with the error message.
	"""
	recipients = ["ravi.patel@mantratec.com","abhishek.jain@mantratec.com","anurag@mantratec.com"]  # Replace with actual recipients
	subject = "Error in Beneficiary File Processing 2"
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
		frappe.logger().info(f"Error email sent to: {recipients}")
	except Exception as email_error:
		frappe.logger().error(f"Failed to send error email: {email_error}")




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

#yhis function for verify a otp
@frappe.whitelist(allow_guest=True)
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

	# if check_otp==otp:
	#     return "Done"

	# return "Error"

	#check Otp
	if start_date < ck_time:
		if check_otp==otp:
			#enquiry(mobile,equipment_id)
			# user=email
			return "Done"
		else:
			return "Error"
	else:
		return "Expired"
	

# this function for ligin
@frappe.whitelist(allow_guest=True)
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
		frappe.respond_as_web_page(("Invalid Request"), (
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
	amount=0
	if payment_entry:
		unique_code=0
		payment_entry_list=[]
		for i in payment_entry:
			payment_entry_list.append(i['name'])
			amount += i['base_paid_amount_after_tax']
		return {"payment_entry_list":payment_entry_list,"amount":amount}
	else:
		return {"payment_entry_list":[],"amount":0}








@frappe.whitelist()
def upload_file(payment_entry_list,bank_account, delimiter=','):
	try :
		if frappe.db.get_value("Bank Integration", bank_account, "bank")=="ICICI Bank Limited":

			if isinstance(payment_entry_list, str):
				payment_entry_list = json.loads(payment_entry_list)


			icici_file_create(bank_account,payment_entry_list,delimiter=',')
			return "Done"
		
		elif frappe.db.get_value("Bank Integration", bank_account, "bank")=="Punjab National Bank":
			pnb_file_create(bank_account,payment_entry_list,delimiter=',')  
		else :
			frappe.throw("Worng Bank Selected")          
	except Exception as e:
		return "Exception"
	
	
#this function is use for a push file in icici snorken folder 
def icici_file_create(bank_account, payment_entry_list, delimiter='|'):
	
	try :
		
		directory = frappe.db.get_value("Bank Integration", bank_account, "file_upload_path")
		# directory = '/home/mantra/Desktop/TestPayment'

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
				remarks = payment_entry.remarks.replace('\n', ' ')[:100] if payment_entry.remarks else ""
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
					debit_ac_no.replace("\n", ""),
					beneficiary_code.replace("\n", ""),
					beneficiary_ac_no.replace("\n", ""), 
					beneficiary_name.replace("\n", ""),
					amt, pay_mod, date, ifsc.replace("\n", ""), 
					payable_location_name, print_location,
					bane_mobile_no, bane_email_id, bane_add1, bane_add2, bane_add3,
					bane_add4, bane_add_detail_1, bane_add_detail_2, bane_add_detail_3,bane_add_detail_4,bane_add_detail_5, remarks.replace("\n", "")
				]
				data_rows.append(new_row)


			if total_amount <= 500000:

				numeric_characters = string.digits
				unique_batch_number = ''.join(random.choices(numeric_characters, k=6))

				current_date = datetime.now()
				formatted_date = current_date.strftime("%d%m%Y")

				file_name = f"MANTRASH2H_MANTRASH2HUP_{formatted_date}_{unique_batch_number}.txt"
				file_path = os.path.join(directory, file_name)


				for payment_entry in party_payment_list:

					#Update value in payment entry
					update_query = "UPDATE `tabPayment Entry` SET `custom_unique_batch_number`='{}', `custom_payment_status_`='Processed', `custom_payment_file_name`='{}' WHERE `name`='{}'".format(unique_batch_number,file_name,payment_entry.name)
					# update_query = "UPDATE `tabPayment Entry` SET `custom_payment_file_name`='{}' WHERE `name`='{}'".format(file_name,payment_entry.name)

					update_query_run = frappe.db.sql(update_query,as_dict=1)
					# frappe.db.set_value("Payment Entry", payment_entry.name, "custom_unique_batch_number", unique_batch_number)
					# frappe.db.set_value("Payment Entry", i, "custom_payment_status_", "Processed")




				# list_items = ast.literal_eval(party_payment_list)


				#Write file in bank folder
				try :
					with open(file_path, 'w', newline='') as file:
						writer = csv.writer(file, delimiter="|")
						writer.writerow(header)
						writer.writerows(data_rows)
				except Exception as e :
					error_mail_send("Payment file write issue.","{} payment file create.<br>{}".format(str(e),str(traceback.format_exc())))
					return e


				try:
					for payment_entry in party_payment_list:
						frappe.db.set_value("Payment Entry", payment_entry.name, "custom_payment_status_", "Processed")
				except Exception as e :
					error_mail_send("Payment file creation issue.","{} payment file create.<br>{}".format(str(e),str(traceback.format_exc())))



		frappe.db.commit()
		return "Done"
	except Exception as e :
		error_mail_send("Payment file creation issue.","{} payment file create. {}".format(str(e),str(traceback.format_exc())))
		return str(traceback.format_exc())

@frappe.whitelist()
def error_mail_send(title,error):
	frappe.sendmail(
		recipients = ["ravi.patel@mantratec.com"],
		message = error,
		subject= title,
	)
	return True

# upload salary slip.txt file on snorkel
@frappe.whitelist()
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

		file_path = os.path.join("/home/mantra/Desktop/", file_name)

		# Fetch Salary Slip details based on Payroll Entry
		salary_slips = frappe.get_all(
			"Salary Slip",
			filters={"payroll_entry": payroll_entry,"docstatus": 1} if payroll_entry else {},
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

		payment_account = frappe.db.get_value("Payroll Entry", payroll_entry, "bank_account") or ""
		debit_ac_no = frappe.db.get_value("Bank Account", payment_account, "bank_account_no") or ""
		
		if debit_ac_no=="":
			frappe.throw("Debit account not found.")


		rows = []
		rows_not_process = []
		for slip in salary_slips:
			# ifsc_code = frappe.db.get_value("Employee", slip["employee"], "ifsc_code") or ""
			date = datetime.today().strftime('%d-%b-%Y')

			# employee_account_no = frappe.db.get_value("Bank Account", payment_account, "bank_account_no") or ""
			# employee_account_no, ifsc_code = frappe.db.get_value('Bank Account', {'party_type': 'Employee','party': slip["employee"],'workflow_state': 'Approved','docstatus': 1}, ['bank_account_no', 'custom_ifsc'])
			employee_account_no=""
			ifsc_code=""
			try:
				employee_account_no = frappe.db.get_value('Bank Account', {'party': slip["employee"],'workflow_state': 'Approved','docstatus': 1}, ['bank_account_no'])
				ifsc_code = frappe.db.get_value('Bank Account', {'party': slip["employee"],'workflow_state': 'Approved','docstatus': 1}, ['custom_ifsc'])
			except Exception as e:
				employee_account_no=""
				ifsc_code=""

			addedInFail = False
			if employee_account_no in ["",None,"Null","None"]:
				rows_not_process.append(slip)
				addedInFail = True

			if ifsc_code in ["",None,"Null","None"]:
				if not addedInFail:
					rows_not_process.append(slip)
					addedInFail = True

			if not addedInFail:
				rows.append([
					debit_ac_no.replace("\n", ""),
					slip["employee"].replace("\n", ""),
					employee_account_no.replace("\n", ""),
					slip["employee_name"].replace("\n", ""),
					slip["net_pay"],
					"N",
					date,
					ifsc_code.replace("\n", ""),
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


		if len(rows_not_process)!=0:
			message = ""
			for slip in rows_not_process:
				message="{}<br>{}".format(message,slip["employee"])

			frappe.sendmail(
				recipients=["abhishek.jain@mantratec.com","ravi.patel@mantratec.com"],
				subject="{} - ({}) entries get issue.".format(payroll_entry,len(rows_not_process)),
				message="Detail of issue record in payroll. It may be reject account or account not created.<br>{}".format(message),
			)
			
			# return message
			frappe.msgprint("There is issue in some record from this payroll. Administrator will get mail with all detail.")

			# print("Error Message","Account no or IFCF code issue with below employee code\n{}".format(message))

			# frappe.throw("Account no or IFCF code issue with below employee code\n{}".format(message))
			# return


		# frappe.throw("File uploaded")
		# return len(rows)

		if len(rows)==0:
			frappe.throw("Not found any entry to process")
			return "Not found any entry to process"

		# with open(file_path, 'w', newline='') as file:
		#     writer = csv.writer(file, delimiter="|")
		#     writer.writerow(headers) 
		#     writer.writerows(rows)  

		# with open(file_path, 'rb') as file:
		#     file_content = file.read()

		# file_doc = frappe.get_doc({
		#     "doctype": "File",
		#     "file_name": file_name,
		#     "file_size": len(file_content),
		#     "attached_to_doctype": "Payroll Entry",
		#     "attached_to_name": payroll_entry,
		#     "content": file_content,
		#     "is_private": True  # Set this to True if you want it to be private
		# })
		# file_doc.save()

		# print(f'File {file_name} created successfully in {directory}.')
		frappe.db.set_value('Payroll Entry', payroll_entry, "custom_salary_slip_file_generated", 1)
		return f"File created successfully: {file_name}"

	except Exception as e:
		frappe.log_error(message=str(e), title="Salary Slip TXT Generation Error")
		frappe.throw("Error\n{}".format(str(traceback.format_exc())))
		return False
		# return str(traceback.format_exc())
		# return str(e)


@frappe.whitelist(allow_guest=True)
def generate_payroll_payment_file(payroll_entry,create_only_file=None):

	reply={}
	reply['message']=""
	reply['status_code']=500
	
	if create_only_file in [None,"","None"]:
		create_only_file = 1
	
	create_only_file = int(create_only_file)

	try:
		if payroll_entry in [None,"","None"]:
			reply['message']="No payroll entry found."
			return reply
		
		if not frappe.db.exists("Payroll Entry", payroll_entry):
			reply['message']="No payroll entry found."
			return reply
		
		payroll_entry_document = frappe.get_doc("Payroll Entry",payroll_entry)     
		if payroll_entry_document.custom_salary_slip_file_generated in [1,True]: 
			reply['message']="Payroll payment entry is already done."
			return reply

		directory_sql = "SELECT file_upload_path FROM `tabBank Integration`"
		directory_list = frappe.db.sql(directory_sql, as_dict=True) 

		if not directory_list:
			reply['message']="Payment file upload path not set in 'Bank Integration'"
			return reply

		directory = directory_list[0].get("file_upload_path")

		if not directory:
			reply['message']="Payment file upload path not set in 'Bank Integration'"
			return reply





		# Fetch Salary Slip details based on Payroll Entry        
		# salary_slips = frappe.get_all(
		#     "Salary Slip",
		#     filters={"payroll_entry": payroll_entry,"docstatus": 1} if payroll_entry else {},
		#     fields=["employee", "employee_name", "net_pay", "bank_name", "bank_account_no", "posting_date", "name"]
		# )

		query = "SELECT employee,employee_name,net_pay,bank_name,bank_account_no,posting_date,name FROM `tabSalary Slip` WHERE `payroll_entry`='{}' AND `docstatus`=1 AND `custom_payment_status` IN ('Fail','Initiated')".format(payroll_entry)
		salary_slips= frappe.db.sql(query,as_dict=1)

		if not salary_slips:
			reply['message']="No salary slips found for the given payroll entry."
			return reply

		payment_account = frappe.db.get_value("Payroll Entry", payroll_entry, "bank_account") or ""
		debit_ac_no = frappe.db.get_value("Bank Account", payment_account, "bank_account_no") or ""
		
		if debit_ac_no=="":
			reply['message']="Debit account not found."
			return reply

		headers = [
			'Debit Ac No', 'beneficiary code', 'Beneficiary Ac No', 'Beneficiary Name',
			'Amt', 'Pay Mod', 'Date', 'IFSC', 'Payable Location name', 'Print Location',
			'Bene Mobile no', 'Bene email id', 'Ben add1', 'Ben add2', 'Ben add3',
			'Ben add4', 'Add details 1', 'Add details 2', 'Add details 3',
			'Add details 4', 'Add details 5', 'Remarks'
		]

		rows = []
		rows_not_process = []
		for slip in salary_slips:

			date = datetime.today().strftime('%d-%b-%Y')
			employee_account_no=""
			ifsc_code=""
			try:
				employee_account_no = frappe.db.get_value('Bank Account', {'party': slip["employee"],'workflow_state': 'Approved','docstatus': 1}, ['bank_account_no'])
				ifsc_code = frappe.db.get_value('Bank Account', {'party': slip["employee"],'workflow_state': 'Approved','docstatus': 1}, ['custom_ifsc'])
			except Exception as e:
				employee_account_no=""
				ifsc_code=""

			addedInFail = False
			if employee_account_no in ["",None,"Null","None"]:
				rows_not_process.append(slip)
				addedInFail = True

			if ifsc_code in ["",None,"Null","None"]:
				if not addedInFail:
					rows_not_process.append(slip)
					addedInFail = True


			# emp_name = str(slip["employee_name"]).replace('/n',''),
			# emp_name = str(emp_name).replace('\n',''),
			# emp_name = str(emp_name).replace('"',''),
			emp_name = str(slip["employee_name"])

			if not addedInFail:
				rows.append([
					debit_ac_no.replace("\n", ""),
					slip["employee"].replace("\n", ""),
					employee_account_no.replace("\n", ""),
					emp_name.replace("\n", ""),
					slip["net_pay"],
					"N",
					date,
					ifsc_code.replace("\n", ""),
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


		account_error = ""
		message = ""
		if len(rows_not_process)!=0:
			message = ""
			for slip in rows_not_process:
				message="{}<br>{}".format(message,slip["employee"])

			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="{} - ({}) entries get issue.".format(payroll_entry,len(rows_not_process)),
				content="Detail of issue record in payroll. It may be reject account or account not created.<br>{}".format(message),
				now = True
			)
			account_error = "<br> Below is the employee list which not include in payment entry due to account issue.<br>{}".format(message)


		if len(rows)==0:
			reply['message']="Not found any entry to process."
			return reply

		# Commente remove
		file_content = ""
		#Write file in testing folder
		# with open(file_path_temp, 'w', newline='') as file:
		#     writer = csv.writer(file, delimiter="|")
		#     writer.writerow(headers) 
		#     writer.writerows(rows)  

		# with open(file_path_temp, 'rb') as file:
		#     file_content = file.read()


		# for row in rows:
		numeric_characters = string.digits
		unique_batch_number = ''.join(random.choices(numeric_characters, k=6))
		current_date = datetime.now()
		formatted_date = current_date.strftime("%d%m%Y")
		file_name = f"MANTRASH2H_MANTRASH2HUP_{formatted_date}_{unique_batch_number}.txt"

		# Commente remove
		file_path_temp = frappe.utils.get_bench_path()+ "/sites/" + frappe.utils.get_path('public', 'payroll', file_name)[2:]
		file_path = os.path.join(directory, file_name)
		# file_path = file_path_temp
		
		#Write in live payment path
		if create_only_file==0:
			with open(file_path, 'w', newline='') as file:
				writer = csv.writer(file, delimiter="|")
				writer.writerow(headers) 
				# writer.writerows([row])
				writer.writerows(rows)

			with open(file_path, 'rb') as file:
				file_content = file.read()

		file_path_temp = frappe.utils.get_bench_path()+ "/sites/" + frappe.utils.get_path('public', 'payroll', file_name)[2:]

		with open(file_path_temp, 'w', newline='') as file:
			writer = csv.writer(file, delimiter="|")
			writer.writerow(headers) 
			# writer.writerows([row])
			writer.writerows(rows)

		with open(file_path_temp, 'rb') as file:
			file_content = file.read()
		try:
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": file_path_temp,
				"file_size": len(file_content),
				"attached_to_doctype": "Payroll Entry",
				"attached_to_name": payroll_entry,
				"content": file_content,
				"is_private": True  # Set this to True if you want it to be private
			})
			file_doc.save()
			
		except Exception as e:
			frappe.sendmail(
				recipients = ["ravi.patel@mantratec.com"],
				message = "{} user have no permission to save record of file.",
				subject= "Payroll payment file save issue in file list.",
				now = True
			)


		if create_only_file==0:
			# Commente remove
			frappe.db.set_value('Payroll Entry', payroll_entry, "custom_salary_slip_file_generated", 1)
			reply['message']="Payment file {} create with {} entry. <br><br> {}".format(file_name,len(rows),account_error)
		else:
			reply['message']="Payment file {} create with {} entry. You can check in left side attachment with same file name. <br><br> {}".format(file_name,len(rows),account_error)

		reply['status_code']=200
		
		return reply
	except Exception as e:
		error = str(traceback.format_exc())
		reply['message']="Error while processing. <br>{}".format(error)
		reply['status_code']=500
		frappe.sendmail(
			recipients = ['ravi.patel@mantratec.com'],
			subject="Error while payroll payment entry",
			content=error,
			now = True
		)

	return reply



#this function is use for a pnb file creation
def pnb_file_create(bank_account, payment_entry_list, delimiter=','):
	try:
		header = ["Payment Method", "Transaction Reference No.", "Value Date", "Debit A/C no", "Debit A/c Currency", "Beneficiary A/c no", "Beneficiary Code", "Bene Name", "Amount Payable", "Beneficiary Bank BIC Code", "Print Branch", "Transaction Status", "Verified By", "UTR No"]

		# Define the directory and file name
		numeric_characters = string.digits
		directory = frappe.db.get_value("Bank Integration", bank_account, "file_upload_path")
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

		test1233=""
		if not recipients:
			test1233="123"
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
				return str(e)
	
	except Exception as e:
		return str(e)









#get revers Mis From Bank PNB
@frappe.whitelist()
def get_pnb_file():
	# Specify the path to your CSV file
	# folder_path = '/home/mantra/Documents/PNB/recive_file'
	bank_list = frappe.db.get_list("Bank Integration", filters={"bank": "Punjab National Bank"}, fields=["name", "bank", "file_pull_path"])
	all_data = []
	for i in bank_list:
	# Initialize an empty list to store data from all files
		folder_path = i["file_pull_path"]
		

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





#get revers Mis From Bank ICICI
@frappe.whitelist()
def get_icici_bank_file(delimiter='|'):
	
	frappe.enqueue(get_bene_file,queue='long',job_name="Beny file process",timeout=100000,delimiter=delimiter)
	frappe.enqueue(get_icici_bank_file_background,queue='long',job_name="ICICI file process",timeout=100000,delimiter=delimiter)
	return True


@frappe.whitelist()
def get_icici_bank_file_background(delimiter='|'):
	
	# errorLog('BENY_CRON2',"",False)

	try:
		# Get the path to the folder containing the files
		folder_path = frappe.db.get_value("Bank Integration", "Mantra - ICICI Bank Limited - 018951000027", "file_pull_path")
		backup_folder = frappe.db.get_value("Bank Integration", "Mantra - ICICI Bank Limited - 018951000027", "file_backup_path")


		one_hour_ago = datetime.now() - timedelta(hours=1)
		filersreturn = []
		for file_name in os.listdir(folder_path):
			csv_file_path = os.path.join(folder_path, file_name)
			modification_time = datetime.fromtimestamp(os.path.getmtime(csv_file_path))
			if modification_time >= one_hour_ago:
				if file_name.endswith('.txt'):
					if not errorLogExites('PAYMENTPROCESSFILE',file_name):
						filersreturn.append(file_name)
						errorLog('PAYMENTPROCESSFILE',file_name,True)


		# filersreturn = []
		# for file_name in os.listdir(folder_path):
		# 	if file_name.endswith('.txt'):
		# 		if not errorLogExites('PAYMENTPROCESSFILE',file_name):
		# 			filersreturn.append(file_name)
		# 			errorLog('PAYMENTPROCESSFILE',file_name,True)

		if len(filersreturn)==0:
			return "No files found."


		data = []
		for file_name in filersreturn:
			csv_file_path = os.path.join(folder_path, file_name)

			if file_name.startswith("585730452"):

				#Call funcation to send in mefron server
				send_file(csv_file_path,file_name)

				previous_file = frappe.get_all("Bank Integration Log",filters=[['file_type', '=', 'Reverse MIS'],['file_name', '=', file_name]])
				if len(previous_file)==0:
					#insert bank transaction log
					doc = frappe.new_doc('Bank Integration Log')
					doc.file_from = "Mefron"
					doc.file_type = "Reverse MIS"
					doc.file_name = file_name
					doc.insert(ignore_permissions=True)
					# frappe.sendmail(
					#     recipients=["ravi.patel@mantratec.com"],
					#     subject="Bene file need to send on mefron server 5",
					#     message="This is bene file send on mefron server {}".format(file_name)
					# )
			else:
				# Open the CSV file and read its contents
				with open(csv_file_path, mode='r') as file:
					for line in file:
						row = line.strip().split(delimiter)
						data.append(row)

			backup_file_path = os.path.join(backup_folder, file_name)
			shutil.move(csv_file_path, backup_file_path)


		if len(data)==0:
			return "No row found to process"


		for data_dict in data:
			if len(data_dict)>15:
				try:
					if frappe.db.exists("Payment Entry", data_dict[15]):

						ERP_status = ""
						rejection_reason = ""


						if data_dict[22] == "Paid" or data_dict[22]=="Authorization Pending" or data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
							if data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
								ERP_status = "Fail"
								rejection_reason = data_dict[22]
							else:
								if data_dict[22] == "Paid":
									ERP_status = "Success"
								else:
									ERP_status = "Authorization Pending"
									rejection_reason = data_dict[22]

							frappe.db.set_value("Payment Entry", data_dict[15], {
								"custom_payment_status_": ERP_status,
								"custom_payment_ref_no": data_dict[21],
								"custom_customer_ref_no": data_dict[24],
								"custom_instrument_no": data_dict[26],
								"custom_instrument_ref_no": data_dict[25],
								"custom_liquidation_date": data_dict[23],
								"custom_utr_no":  data_dict[27],
								"custom_rejection_reason":rejection_reason,
								# "docstatus": docstatus
							})
							
							
							#If fail then need to reject
							if ERP_status == "Fail":
								current_user = frappe.session.user
								frappe.set_user("Administrator")
								doc = frappe.get_doc("Payment Entry",data_dict[15])
								doc.cancel()
								
								# frappe.db.set_value("Payment Entry", data_dict[15], {
								#     "workflow_state": "Cancelled",
								# })
								frappe.set_user(current_user)
								query = "UPDATE `tabPayment Entry` SET `workflow_state`='Cancelled' WHERE `name`='{}'".format(data_dict[15])
								update_work_flow_state = frappe.db.sql(query, as_dict=True) 
							
							if ERP_status == "Success":
								document = frappe.get_doc("Bank Integration", "Mantra - ICICI Bank Limited - 018951000027")
								if document.custom_sent_payment_advice == 1:

									query = "SELECT custom_payment_advice_send FROM `tabPayment Entry` WHERE `name`='{}'".format(data_dict[15])
									mdf = frappe.db.sql(query, as_dict=True)
									if len(mdf)!=0:
										if mdf[0]['custom_payment_advice_send'] in [0,'0',False]:
											send_payment_advice_email(data_dict[0], data_dict[3], data_dict[5], data_dict[20], data_dict[1], data_dict[27], data_dict[4], data_dict[6], data_dict[28], data_dict[3],data_dict[25], data_dict[15],"")


					elif frappe.db.exists("Salary Slip", data_dict[15]):

						ERP_status = ""
						rejection_reason = ""

						if data_dict[22] == "Paid" or data_dict[22]=="Authorization Pending" or data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
							if data_dict[22]=="Expired or Rejected by Authorizer/Confirmer":
								ERP_status = "Fail"
								rejection_reason = "Rejected"
								
								query = "SELECT payroll_entry FROM `tabSalary Slip` WHERE `name`='{}'".format(data_dict[15])
								list_payroll = frappe.db.sql(query, as_dict=True)
								if len(list_payroll)!=0:
									query = "UPDATE `tabPayroll Entry` SET `custom_salary_slip_file_generated`=0 WHERE `name`='{}'".format(list_payroll[0]['payroll_entry'])
									update_payroll_entry = frappe.db.sql(query, as_dict=True)

									frappe.sendmail(
										recipients = 'abhishek.jain@mantratec.com',
										subject = 'Salary not process : {} - Payroll : {}'.format(data_dict[15],list_payroll[0]['payroll_entry']),
										message = 'This salary slip is not process from bank side.',
									)
					
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

							rejection_reason=""
							if data_dict[24]=="P":
								rejection_reason = data_dict[25]
							else:
								rejection_reason = data_dict[24]

							query = "UPDATE `tabPayment Entry` SET `custom_payment_status_`='Fail', `custom_rejection_reason`='{}' WHERE `name`='{}'".format(str(rejection_reason)[0:110],str(data_dict[17]))
							update_work_flow_state = frappe.db.sql(query, as_dict=True) 

							current_user = frappe.session.user
							frappe.set_user("Administrator")
							doc = frappe.get_doc("Payment Entry",data_dict[17])
							doc.cancel()
							frappe.set_user(current_user)
							query = "UPDATE `tabPayment Entry` SET `workflow_state`='Cancelled' WHERE `name`='{}'".format(str(data_dict[17]))
							update_work_flow_state = frappe.db.sql(query, as_dict=True) 


						elif frappe.db.exists("Salary Slip", data_dict[17]):

							if data_dict[24]=="P":
								frappe.db.set_value("Salary Slip", data_dict[17], {
									"custom_rejection_reason":data_dict[25],
									"custom_payment_status": "Fail",
								})
							elif data_dict[23]=="P":
								frappe.db.set_value("Salary Slip", data_dict[17], {
									"custom_rejection_reason":data_dict[24],
									"custom_payment_status": "Fail",
								})                                
							else:
								frappe.db.set_value("Salary Slip", data_dict[17], {
									"custom_payment_status": "Fail",
								})
								
							query = "SELECT payroll_entry FROM `tabSalary Slip` WHERE `name`='{}'".format(data_dict[17])
							list_payroll = frappe.db.sql(query, as_dict=True)
							if len(list_payroll)!=0:
								query = "UPDATE `tabPayroll Entry` SET `custom_salary_slip_file_generated`=0 WHERE `name`='{}'".format(list_payroll[0]['payroll_entry'])
								update_payroll_entry = frappe.db.sql(query, as_dict=True)

								frappe.sendmail(
									recipients = 'abhishek.jain@mantratec.com',
									subject = 'Salary not process : {} - Payroll : {}'.format(data_dict[17],list_payroll[0]['payroll_entry']),
									message = 'This salary slip is not process from bank side.',
								)

				except KeyError as ke:
					error_message = f"KeyError: {ke} <br> traceable: {str(traceback.format_exc())} in file {file_name}"
					send_icici_bank_file_error_email(error_message,"KeyError line 1365")

				except Exception as e:
					error_message = f"An error occurred while processing data_dict: {e} <br> traceable: {str(traceback.format_exc())} in file {file_name}"
					send_icici_bank_file_error_email(error_message,"processing line 1369")
		
	except Exception as e:
		error_message = f"An error occurred in the get_icici_bank_file function: {e} <br> traceable: {str(traceback.format_exc())}"
		send_icici_bank_file_error_email(error_message,"Exception line 1663")


def send_icici_bank_file_error_email(error_message,title=None):
	"""
	Sends an email with the error message.
	"""
	recipients = ["mailto:ravi.patel@mantratec.com"]
	subject = "Error in ICICI Bank File Processing".format(str(title))
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
	except Exception as email_error:
		return str(email_error)



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
			recipients = 'abhishek.jain@mantratec.com',
			subject = 'Subject of the Email',
			message = 'Body of the email',
			attachments=attachments
		)
		send = flush()
	except Exception as e:
		return e



@frappe.whitelist()
def send_file(file_path,file_name):


	if not file_name.startswith("585730452"):
		frappe.sendmail(
			recipients = 'ravi.patel@mantratec.com',
			subject = 'File try to send on mefron which is related to mantra',
			message = '{}-{}'.format(file_path,file_name),
		)
		return


	
	# URL to send the POST request
	url = "http://192.168.5.56:8008/api/method/mefron_dev.backend_code.api.recive_file"

	# Path to the file to be uploaded
	try:
		# Open the file in binary mode
		with open(file_path, "rb") as file:
			# Prepare the file payload
			files = {"file": file}
			data = {"file_type": "Reverse MIS"}
			# Send POST request
			response = requests.post(url, files=files, data=data)
			
			if response.status_code == 200:
				# print("File uploaded successfully!")
				mefron_files = frappe.db.sql('''select file_name from `tabBank Integration Log` where file_from="Mefron"''',as_list=True)
				count = 0
				for i in mefron_files:
					if i[0] == file_name:
						count = count+1
				# mefron_files = frappe.get_all('Bank Integration Log',filters={'file_from': 'Mefron'},fields=['file_name'],as_list=True)
				if count != 0:
					pass
				else:
					doc = frappe.new_doc('Bank Integration Log')
					doc.file_from = "Mefron"
					doc.file_type = "Reverse MIS"
					doc.file_name = file_name
					doc.insert(ignore_permissions=True)
			else:

				recipients = ["ravi.patel@mantratec.com"]
				subject = "Error in Beneficiary File Processing 1772"
				message = f"""
				<p>Dear User,</p>
				<p>An error occurred during the execution of the scheduled task:</p>
				<p>{response.text}</p>
				<p>Please check the logs and take necessary action.</p>
				"""
				frappe.sendmail(
					recipients=recipients,
					subject=subject,
					message="{}<br>{}".format(message,str(traceback.format_exc()))
				)
	except Exception as e:
		recipients = ["ravi.patel@mantratec.com"]
		subject = "Error in Beneficiary File Processing : Using send file"
		message = f"""
		<p>Dear User,</p>
		<p>An error occurred during the execution of the scheduled task:</p>
		<p>{e}</p>
		<p>Please check the logs and take necessary action.</p>
		"""
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message="{}<br>{}".format(message,str(traceback.format_exc()))
		)



@frappe.whitelist()
def send_payment_advice_payment_entry(payment_entry,email):
	
	# payment_entry = 'ACC-PAY-2025-03504'
	if not frappe.db.exists("Payment Entry",payment_entry):
		frappe.sendmail(
			recipients=["abhishek.jain@mantratec.com","ravi.patel@mantratec.com"],
			subject="Payment entry not found",
			message=payment_entry,
		)
		return payment_entry

	document = frappe.get_doc("Payment Entry",payment_entry)
	debit_account_no = frappe.db.get_value("Bank Account", document.bank_account, "bank_account_no") or ""

	amount = document.base_paid_amount_after_tax
	date = document.custom_liquidation_date
	remarks = document.remarks

	benfiecery_account_no = frappe.db.get_value("Bank Account", document.party_bank_account, "bank_account_no") or ""

	utr_no = document.custom_utr_no
	payment_mode = document.mode_of_payment
	ifsc_code = frappe.db.get_value("Bank Account", document.party_bank_account, "custom_ifsc") or ""
	benifecery_code = document.party
	benifecery_name = document.party_name
	instrument_ref_no = document.custom_instrument_ref_no
	payment_entry = document.name
	send_payment_advice_email(debit_account_no,amount,date,remarks,benfiecery_account_no,utr_no,payment_mode,ifsc_code,benifecery_code,benifecery_name,instrument_ref_no,payment_entry,email)

	return "Payment advice send on {}".format(email)



@frappe.whitelist()
def send_payment_advice_email(debit_account_no, amount, date, remarks, benfiecery_account_no, utr_no, payment_mode, ifsc_code, benifecery_code, benifecery_name, instrument_ref_no, payment_entry,email):
	
	# email = ""
	if amount:
		rupees, paise = divmod(round(float(amount) * 100), 100)
			
		# Convert rupees and paise to words
		rupees_in_words = num2words(rupees, lang='en_IN')
		paise_in_words = num2words(paise, lang='en_IN') if paise > 0 else None
		
		# Construct the final string
		if paise_in_words:
			amount_words =  f"{rupees_in_words.capitalize()} rupees and {paise_in_words} paise"
		else:
			amount_words = f"{rupees_in_words.capitalize()} rupees"
	
	debit_account_no if debit_account_no else "-"
	amount if amount else "-"
	date if date else "-"
	remarks if remarks else "-"
	benfiecery_account_no if benfiecery_account_no else "-"
	utr_no if utr_no else "-"
	payment_mode if payment_mode else "-"
	ifsc_code if ifsc_code else "-"
	benifecery_code if benifecery_code else "-"

	#Get beneficary name
	# benifecery_name if benifecery_name else "-"
	# if beneficiary_name in ['-',' ',None,'None','null']:
	benifecery_name = '-'
	if benifecery_code not in ['-',' ',None,'None','null']:
		directory_sql = "SELECT supplier_name FROM `tabSupplier` WHERE `name`='{}'".format(benifecery_code)
		directory_list = frappe.db.sql(directory_sql, as_dict=True)
		if len(directory_list)!=0:
			benifecery_name = directory_list[0]['supplier_name']


	instrument_ref_no if instrument_ref_no else "-"
	payment_entry if payment_entry else "-"
	
		
	
	if not frappe.db.exists("Payment Entry",payment_entry):
		frappe.sendmail(
			recipients=["abhishek.jain@mantratec.com","ravi.patel@mantratec.com"],
			subject="Error in payment advice",
			message="Payment advice not send becuase payment entry is remove from system. payment entry number {} <br>debit_account_no:{}<br>amount:{}<br>benfiecery_account_no:{}<br>utr_no:{}".format(payment_entry,debit_account_no,amount,benfiecery_account_no,utr_no),
		)
		return



	document = frappe.get_doc("Payment Entry",payment_entry)
	if email=="":
		email = document.contact_email if document.contact_email else ""


	invoices = []

	if document.references:
		for i in document.references:
			d = frappe.get_doc(i.reference_doctype, i.reference_name)
			
			t_date = ""
			if i.reference_doctype in ["Purchase Invoice","Employee Advance","Expense Claim","Journal Entry"]:
				t_date = d.posting_date
			else:
				t_date = d.transaction_date

			x = {
				"document_no": i.reference_name,
				"invoice_no": i.bill_no if i.bill_no else "-",
				"invoice_date": t_date,
				"paid_amount":i.allocated_amount
			}
			invoices.append(x)
		else:
			x = {
				"document_no": "-",
				"invoice_no": "-",
				"invoice_date": "-",
				"paid_amount":"-",
			}

	payment_data = {
		# "customer_ref_no": instrument_ref_no,
		"company_logo": "",  # Path to the ABC Limited Group logo
		"bank_logo": "",  # Path to the ICICI Bank logo
		"account_no": debit_account_no if debit_account_no else "-",
		"value_date": date if date else "-",
		"beneficiary_code": benifecery_code if benifecery_code else "-",
		"beneficiary_name": benifecery_name if benifecery_name else "-",
		"beneficiary_account_no": benfiecery_account_no if benfiecery_account_no else "-",
		"payment_doc_no": payment_entry,
		"payment_mode": payment_mode if payment_mode else "-",
		"bank_reference_no": instrument_ref_no if instrument_ref_no else "-",
		"utr_no": utr_no if utr_no else "-",
		"remarks": remarks if remarks else "-",
		"additional_details": "-",
		"ifsc_code": ifsc_code if ifsc_code else "-",
		"amount": amount,
		"amount_words": amount_words if amount_words else "-",
		"invoices": invoices if invoices else "-"
	}

	# Step 1: Prepare the exact HTML layout
	html_content = f"""
		<!DOCTYPE html>
		<html>
		<head>
			<title>Payment Advice</title>
			<style>
				.content {{
				text-align: center;
				margin: 20px 0;
			}}
			.container {{
				width: 80%;
				margin: 20px auto;
				border: 1px solid #ddd;
				padding: 20px;
				box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
			}}
			body {{
				font-family: Courier New, Courier, Arial, sans-serif;
				font-size: 12px;
				margin: 20px;
			}}
			.header {{
			text-align: center;
			margin-bottom: 20px;
			}}
			.header img {{
			height: 50px;
			margin: 0 10px;
			}}
			.details {{
				width: 100%;
				margin-bottom: 10px;
				border: none;
			}}
			.details td, .details th {{
				font-size: 9px;
				padding: 5px;
				text-align: left;
				vertical-align: top;
				border: none;
			}}
			.details th {{
				font-weight: bold;
				white-space: nowrap;
			}}
			.summary {{
				width: 100%;
				border-collapse: collapse;
				margin-top: 10px;
			}}
			.summary th, .summary td {{
				font-size: 9px;
				padding: 5px;
				border: 1px solid #000;
				text-align: left;
			}}
			.summary th {{
				background-color: #f2f2f2;
			}}
			.footer {{
				text-align: center;
				font-size: 8px;
				margin-top: 20px;
				color: #555;
			}}
			</style>
			</head>
			<body style="font-family: 'Courier New', 'Courier', 'Arial', 'sans-serif';">
			
			<table style="border-collapse: collapse; width: 100%;" border="0px">
			<tbody>
			<tr>
			<td style="width: 33.3333%; text-align: center;"><img style="float: left;" src="http://192.168.1.38:8001/files/images.png" alt="" width="188" height="97" /></td>
			<td style="width: 33.3333%; border-style: none;">
			<h4 style="text-align: center; margin-bottom: 20px;">Mantra Softech India Pvt Ltd</h4>
			<p style="text-align: center;">B 203, SHAPATH HEXA, NEAR GUJARAT HIGH COURT, S G
		HIGHWAY SOLA,<br>AHMEDABAD, GUJARAT, 380060</p>
			<p style="text-align: center;"></p>
			<p style="text-align: center;"></p>
			<p style="text-align: center;"></p>
			<p style="text-align: center;"></p>
			</td>
			<td style="width: 33.3333%;"><img style="float: right;" src="http://192.168.1.38:8001/files/Mantra-Logo_1.png" alt="" width="200" /></td>
			</tr>
			</tbody>
			</table>


				<!-- Payment Advice Title -->
				<h3 style="text-align: center; margin-bottom: 20px; text-decoration: underline;">Payment Advice</h3>
				
				<!-- Details Table -->
				<table class="details" style="border : 1px solid black">
					<tr>
						<th>Account No.</th><td>:</td><td>{payment_data['account_no']}</td>
						<th>Value Total</th><td>:</td><td>{payment_data['amount']}</td>
						<th>Value Date</th><td>:</td><td>{payment_data['value_date']}</td>
					</tr>
				</table>
				<table class="details">
					<tr>
						<td>Beneficiary Code</td><td>:</td><td>{payment_data['beneficiary_code']}</td>
						<td>Beneficiary Account No.</td><td>:</td><td>{payment_data['beneficiary_account_no']}</td>
					</tr>
					<tr>
						<td>Beneficiary Name</td><td>:</td><td>{payment_data['beneficiary_name']}</td>
						<td>Payment Document No.</td><td>:</td><td>{payment_data['payment_doc_no']}</td>
					</tr>
					<tr>
						<td>Payment Mode</td><td>:</td><td>{payment_data['payment_mode']}</td>
						<td>Bank Reference No.</td><td>:</td><td>{payment_data['bank_reference_no']}</td>
					</tr>
					<tr>
						<td>UTR No.</td><td>:</td><td>{payment_data['utr_no']}</td>
					</tr>
				</table>
				
				<!-- Message Section -->
				<p>
					Dear Sir/Madam,<br>
					We have initiated your payment through {payment_data['payment_mode']} with Beneficiary Account No. 
					{payment_data['beneficiary_account_no']} and IFSC {payment_data['ifsc_code']} for the value of ₹{payment_data['amount']} 
					({payment_data['amount_words']}) for the services rendered as mentioned below.
				</p>
				
				<!-- Summary Table -->
				<table class="summary">
					<thead>
						<tr>
							<th>Document No.</th>
							<th>Invoice No.</th>
							<th>Invoice Date</th>
							<th>Paid Amount</th>
						</tr>
					</thead>
					<tbody>
		"""

	# Add dynamic rows for invoices
	for invoice in payment_data['invoices']:

		if invoice != "-":
			allkeys = invoice.keys()
			document_no = ""
			invoice_no = ""
			invoice_date = ""
			paid_amount = ""
			if "document_no" in allkeys:
				document_no = str(invoice['document_no'])
			if "invoice_no" in allkeys:
				invoice_no = str(invoice['invoice_no'])
			if "invoice_date" in allkeys:
				invoice_date = str(invoice['invoice_date'])        
			if "paid_amount" in allkeys:
				paid_amount = str(invoice['paid_amount'])        
			
			html_content += f"""
			<tr>
				<td>{document_no}</td>
				<td>{invoice_no}</td>
				<td>{invoice_date}</td>
				<td>₹{paid_amount}</td>
			</tr>
			"""
	
	
	
	
	
	
	
	
	
	
	
	# Close table and add footer
	html_content += f"""
			</tbody>
		</table>
		
		<!-- Footer Section -->
		<div class="footer" style="text-align:left">
			Regards<br>Mantra Treasury Team
		</div>
		<div class="footer" style="text-align:left">
			Note : Actual Transaction date may vary based on the actual bank statement.
		</div>
		<div class="footer">
			This is a computer-generated advice and does not require a signature.
		</div>
	
	</body>
	</html>
	"""


	message = "Please find the attached payment advice."
	subject = "Payment Advice : {} Amount: {}".format(payment_data['beneficiary_name'],payment_data['amount'])
	
	if frappe.db.exists("Email Template","Payment Advice"):
		doc_args = {"supplier_name": benifecery_name,}
		email_template = frappe.get_doc("Email Template", "Payment Advice")
		message = frappe.render_template(email_template.response, doc_args)
		subject = frappe.render_template(email_template.subject)    
	




	# Step 2: Generate PDF from the HTML
	pdf_data = get_pdf(html_content)
	# frappe.log_error("Email send subjecct",subject)

	# Step 3: Send email with PDF attachment
	try:
		if email:
			frappe.sendmail(
				recipients=[email],
				subject=subject,
				message=message,
				attachments=[{
					'fname': f"Payment_Advice_{payment_data['account_no']}.pdf",
					'fcontent': pdf_data
				}]
			)
			send = flush()
			frappe.msgprint(f"Payment advice email sent successfully to {email}.")

			#update payment entry mail tick so its send once only
			query = "UPDATE `tabPayment Entry` SET `custom_payment_advice_send`=1 WHERE `name`='{}'".format(payment_entry)
			mdf = frappe.db.sql(query, as_dict=True)
			# frappe.log_error("Email send","")

		else:
			frappe.sendmail(
				recipients=["abhishek.jain@mantratec.com"],
				subject="Supplier email not found in payment entry {}".format(document.name),
				message="Please find the attached payment advice for payment entry.",
				attachments=[{
					'fname': f"Payment_Advice_{payment_data['account_no']}.pdf",
					'fcontent': pdf_data
				}]
			)
	except Exception as e:
		frappe.sendmail(
			recipients=['ravi.patel@mantratec.com'],
			subject="Payment advice error",
			message="{}<br>{}".format(str(e),str(traceback.format_exc())),
			attachments=[{
				'fname': f"Payment_Advice_{payment_data['account_no']}.pdf",
				'fcontent': pdf_data
			}]
		)