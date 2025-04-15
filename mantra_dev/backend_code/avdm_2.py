import frappe # type: ignore
from frappe import _ # type: ignore
from frappe.utils import nowdate # type: ignore
import json
import traceback
import requests # type: ignore
from mantra_dev.backend_code.globle import errorLog,errorLogExites # type: ignore
import ast
from requests.auth import HTTPBasicAuth # type: ignore


delivery_note_number_proccess = []
key_token = "TOKENAVDM"
key_token_pratham = "TOKENAVDMPRATHAM"
key_body_process = "BODYPROCESSAVDM"
key_serial_no = "SERIALNOAVDM"
key_sub_serial_no = "SUBSERIALNO"
key_dc_no = "DCNOAVDM"
# email_send = False

@frappe.whitelist()
def login_to_avdm_scheduled():
	frappe.enqueue(login_to_avdm, queue='long', timeout=3600,transaction_date=nowdate())
	return True  

@frappe.whitelist(allow_guest=True)
def process_to_avdm_for_date(transaction_date):
	return login_to_avdm(transaction_date)

@frappe.whitelist()
def login_to_avdm(transaction_date):
    
	delivery_note_number_proccess = [] #reset globle variable
 
	errorLog('AVDM-Start',transaction_date,False)
	reply={}

	if frappe.db.get_single_value("AVDM Setting", "enable") == 1:
		
		dc_list = frappe.get_all("Delivery Note", filters={"posting_date": transaction_date, "docstatus": 1, "is_return": 0})
  
		if len(dc_list)==0:
			reply['message']="no delivery note found"
			return reply

		try:
			generate_token()
			generate_token_pratham()
			process_dc_list(dc_list)

			errorLog('AVDM-End',transaction_date,False)
			return reply

		except Exception as e:
			reply['message']="Exception"
			reply['message_traceback']=str(traceback.format_exc())
			mssage = str(traceback.format_exc())
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="AVDM not process due to exception",
				message="avdm.py - login_to_avdm <br>{}".format(mssage)
			)
	else:
		reply['message']="AVDM setting is not enable"
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="AVDM settings is not enable",
			message="avdm.py - login_to_avdm"
		)
		
	return reply   

# @frappe.whitelist(allow_guest=True)
# @frappe.whitelist()
def generate_token():
	
	reply={}
 
	username = frappe.db.get_single_value("AVDM Setting", "username")
	password = frappe.db.get_single_value("AVDM Setting", "password")

	login_url = "https://erptoavdm.aadhaardevice.com/ErptoAVDM/Login"
	login_headers = {
		"accept": "application/json",
	}
	login_body = {
		"username": username,
		"password": password
	}
	response = requests.post(login_url, headers=login_headers, json=login_body)

	# Check if the response content is in bytes and decode it
	response_content = response.content
	if isinstance(response_content, bytes):
		response_content = response_content.decode('utf-8')
	
	response_json = json.loads(response_content)
	details = response_json["details"]
	api_token = details["_APIToken"]
	
	reply['api_token']=api_token

#Delete token and resave in list
	query = "DELETE FROM `tabError Log` WHERE method='{}' LIMIT 1".format(key_token)
	records = frappe.db.sql(query,as_dict=1)
	errorLog(key_token,str(api_token))
 
	return "Token generated and save in log"


@frappe.whitelist(allow_guest=True)
def generate_token_pratham():
	
	reply={}
 
	# username = frappe.db.get_single_value("AVDM Setting", "username")
	# password = frappe.db.get_single_value("AVDM Setting", "password")

	username = "ConsumeDetailsUser"
	password = "bDFsSUhaTjlQU0FRdDhY"

	url = "http://prathamapi.mantratecapp.com/production/api/Authenticate/Login"

	payload = json.dumps({
		"DeviceType": "A"
	})
	headers = {
		'Content-Type': 'application/json',
	}

	response = requests.post(url, headers=headers, data=payload,auth=HTTPBasicAuth(username, password))
 
	response_content = response.content
	if isinstance(response_content, bytes):
		response_content = response_content.decode('utf-8')
	
	response_json = json.loads(response_content)
 
	details = response_json["entityObject"]
	api_token = details["AuthToken"]
	
	reply['api_token']=api_token

	#Delete token and resave in list
	query = "DELETE FROM `tabError Log` WHERE method='{}' LIMIT 1".format(key_token_pratham)
	records = frappe.db.sql(query,as_dict=1)
	errorLog(key_token_pratham,str(api_token))
 
	return reply




@frappe.whitelist(allow_guest=True)
def date_convert(timestamp):
	# timestamp = "2025-02-11T10:59:20.348062Z"
	# timestamp = "2025-02-11T9:59:20.3480264422Z"
	date_part, time_part = timestamp.split("T")
	time_part, microseconds = time_part.split(".")
	hours, minutes, seconds = time_part.split(":")
	hours = hours.zfill(2)
	formatted_timestamp = f"{date_part}T{hours}:{minutes}:{seconds}.{microseconds}"
	return formatted_timestamp

@frappe.whitelist()
def process_dc_list(dc_list):

	reply={}
    
	if frappe.db.get_single_value("AVDM Setting", "enable") == 1:

		reply['setting_enable']="yes"
		try:
			body = []
			for dc in dc_list:
				dc_doc = frappe.get_doc("Delivery Note", dc)
				dc_item = dc_doc.items
				for i in dc_item:
					if i.custom_abdm_enable == 1 and i.custom_reference_model_no:
						if i.serial_no:
							sr_no = i.serial_no
							serial_no = sr_no.replace("\n", ",")
							serial_no_list = serial_no.split(",")

							for s_no in serial_no_list:
								data = {
									"mastCode": "0",
									"serialNo": str(s_no),
									"custName": str(dc_doc.customer_name),
									"dcNo": str(dc_doc.name),
									"dcDate": f"{dc_doc.posting_date}T{dc_doc.posting_time}Z",
									"model": str(i.custom_reference_model_no),
									"subModelType": "0"
								}
								body.append(data)
								data['item_code']=i.item_code
								errorLog(key_sub_serial_no,str(data)) # Add serial number to check for sub serial number

			cunk_size = 100

			body_send = []
			record_found = False

			for index, record in enumerate(body):
				# if index<=50:
				body_send.append(record)
				if index%cunk_size==0:
					reply['chunk_send_{}'.format(str(index))]="Cunk Send"
					errorLog(key_body_process,str(body_send))
					record_found = True
					body_send = []

			if len(body_send)!=0:
				record_found = True
				errorLog(key_body_process,str(body_send))

			#If any record is found then 5 min cron set on
			if record_found:
				query = "UPDATE `tabScheduled Job Type` SET `stopped`=0 WHERE `method` = '{}'".format('mantra_dev.backend_code.avdm.process_one_record')
				records = frappe.db.sql(query,as_dict=1)

			return reply

		except Exception as e:
			reply['message']="Exception"
			reply['message_traceback']=str(traceback.format_exc())
			mssage = str(traceback.format_exc())
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="AVDM not process due to exception-Delivery note",
				message="avdm.py - process_dc_list <br>{}".format(mssage)
			)
	else:
		reply['message']="AVDM setting is not enable"
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="AVDM settings is not enable",
			message="avdm.py - process_dc_list"
		)
		
	return reply


def add_sub_serial_no_entry(data):
	errorLog(key_sub_serial_no,str(data))
	return True







@frappe.whitelist(allow_guest=True)
def process_one_record():

	frappe.enqueue(process_one_record_background, queue='long', timeout=3600)
	return "process start in background"

@frappe.whitelist(allow_guest=True)
def process_one_record_background():
	
	reply= {}
	try:
		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 4".format(key_body_process)
		list_body_to_process = frappe.db.sql(query,as_dict=1)
	
		#If all body process then start update serial no in DB
		if len(list_body_to_process)==0:
			
			#Start fetching sub-serial no
			query = "SELECT error from `tabError Log` WHERE method='{}' LIMIT 1".format(key_sub_serial_no)
			serial_subserial_no_list = frappe.db.sql(query)
			if len(serial_subserial_no_list)!=0:
				return fetch_sub_serial_no_records()

			#Start update serial no in database
			query = "SELECT error from `tabError Log` WHERE method='{}' LIMIT 1".format(key_serial_no)
			serial_no_list = frappe.db.sql(query)			
			if len(serial_no_list)!=0:
				return update_serial_no_records(500)

			# Serial no update record not found then start dn record update
			query = "SELECT error from `tabError Log` WHERE method='{}' LIMIT 1".format(key_dc_no)
			dn_no_list = frappe.db.sql(query)
			if len(dn_no_list)!=0:
				return update_delivery_note_records()
 				
			#stop cron all record are process
			query = "UPDATE `tabScheduled Job Type` SET `stopped`=1 WHERE `method` = '{}'".format('mantra_dev.backend_code.avdm.process_one_record')
			dn_no_list = frappe.db.sql(query)
			return "All task are done cron stop call"


		frappe.enqueue(update_serial_no_records, queue='long', timeout=3600,limit=200)
		frappe.enqueue(fetch_sub_serial_no_records, queue='long', timeout=3600)


		#Process for registration
		creating_url = "https://erptoavdm.aadhaardevice.com/ErptoAVDM"
	
		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 1".format(key_token)
		token = frappe.db.sql(query,as_dict=1)
	
		if len(token)==0:
			generate_token()
			return "Token not found"
	
		headers = {
			"accept": "application/json",
			"Authorization": f"Bearer {token[0]['error']}"
		}
	
		for process_record in list_body_to_process:
			frappe.enqueue(process_request, queue='long', timeout=3600,process_record=process_record,creating_url=creating_url,headers=headers)

	except Exception as e:
			reply['message']="Exception"
			reply['message_traceback']=str(traceback.format_exc())
			mssage = str(traceback.format_exc())
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="AVDM not process due to issue",
				message="avdm.py - process_one_record <br>{}<br>{}".format(mssage,str(reply))
			)
			
	return reply

@frappe.whitelist(allow_guest=True)
def process_request(process_record,creating_url,headers):
    
	reply={}
    
	try:
		body_pass = ast.literal_eval(process_record['error'])
		process_dc_of_serial={}
		body_pass_avdm = []
		for s_no_data in body_pass:
			process_dc_of_serial[s_no_data['serialNo']]=s_no_data['dcNo']
			s_no_data['dcDate'] = date_convert(s_no_data['dcDate'])
			if int(s_no_data['model']) != 13:
				body_pass_avdm.append(s_no_data)

		if len(body_pass_avdm)==0:
			#Once process delete record from error log
			query = "DELETE FROM `tabError Log` WHERE `name`='{}'".format(process_record['name'])
			records_deleted = frappe.db.sql(query,as_dict=1)
			reply['request_url']="No serial no match"
			return reply

		reply['request_url']=creating_url
		reply['request_header']=headers
		reply['request_body']=body_pass_avdm
		
		response1 = requests.post(creating_url, headers=headers, json=body_pass_avdm)
		reply['resposne_status_code']=response1.status_code
		
		dc_response_content = response1.content
		if isinstance(dc_response_content, bytes):
			dc_response_content = dc_response_content.decode('utf-8')
		reply['resposne_contennt']=dc_response_content

		if response1.status_code==200:

			#Once process delete record from error log
			query = "DELETE FROM `tabError Log` WHERE `name`='{}'".format(process_record['name'])
			records_deleted = frappe.db.sql(query,as_dict=1)

			#Get all serial number response in this.
			dc_response_json = json.loads(dc_response_content)
			reply['response']=dc_response_json
			
			if dc_response_json:
				process_dc_no = []

				error_searial_no = []
				for i in dc_response_json:
					if int(i['errorCode'])==0:
						errorLog(key_serial_no,str(i['devicesr']))
						if process_dc_of_serial[i['devicesr']] not in delivery_note_number_proccess:
							process_dc_no.append(process_dc_of_serial[i['devicesr']])
							delivery_note_number_proccess.append(process_dc_of_serial[i['devicesr']])
					else:
						error_searial_no.append(str(i['devicesr']))
						# frappe.enqueue(update_serial_no_field,queue='long',job_name="Update serial no {}".format(i['devicesr']),timeout=100000,serial_no=i['devicesr'])

				for dc_no in process_dc_no:
					errorLog(key_dc_no,str(dc_no))
					# frappe.enqueue(update_delivery_field,queue='long',job_name="Update delivery note {}".format(str(dc_no)),timeout=100000,dc_no=str(dc_no))

				#Get all serial no with error reponse
				if len(error_searial_no)!=0:
					email_serial_no_with_error = []
					for s_no_data in body_pass:
						if str(s_no_data['serialNo']) in error_searial_no:
							email_serial_no_with_error.append(s_no_data)

					if len(email_serial_no_with_error)!=0:
						frappe.sendmail(
							recipients=["ravi.patel@mantratec.com"],
							subject="Serial no with error response",
							message="{}".format(str(email_serial_no_with_error))
						)
		else:
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="EVDM request process error",
				message="{}".format(str(reply))
			)
	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		mssage = str(traceback.format_exc())
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="AVDM not process due to issue",
			message="avdm.py - process_one_record <br>{}<br>{}".format(mssage,str(reply))
		)
  
	return reply





@frappe.whitelist(allow_guest=True)
def fetch_sub_serial_no_records():
	reply={}
    
	try:
		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 50".format(key_sub_serial_no)
		list_body_to_process = frappe.db.sql(query,as_dict=1)
	
		searil_no_pass = []
		record_to_be_proccess = []		
		for process_record in list_body_to_process:
			body_pass = ast.literal_eval(process_record['error'])
			record_to_be_proccess.append(body_pass)
			# for s_no_data in body_pass:
			searil_no_pass.append(body_pass['serialNo'])
	
	
		#Process for sub serial no
		creating_url = "http://prathamapi.mantratecapp.com/Production/api/Product/GetConsumeSerialNoDetails"

		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 1".format(key_token_pratham)
		token = frappe.db.sql(query,as_dict=1)

		if len(token)==0:
			generate_token_pratham()
			return "Token not found"

		headers = {
			"accept": "application/json",
			"Token": token[0]['error']
		}
  
		reply['request_url']=creating_url
		reply['request_header']=headers
		reply['request_body']=searil_no_pass  

		response1 = requests.post(creating_url, headers=headers, json=searil_no_pass)
		reply['resposne_status_code']=response1.status_code
		dc_response_content = response1.content
		if isinstance(dc_response_content, bytes):
			dc_response_content = dc_response_content.decode('utf-8')
		reply['resposne_contennt']=dc_response_content

		if response1.status_code==200:
			#Get all serial number response in this.
			dc_response_json = json.loads(dc_response_content)
			reply['response']=dc_response_json
			if len(dc_response_json)!=0:
				body=[]
				all_serial_no_response = recoursion_all_serial_no(dc_response_json)
				process_serial_no = all_serial_no_response.keys()
				#Check all parent serial no
				for sr_no in process_serial_no:
					#Find serial no from pass list
					for sr_no_record in record_to_be_proccess:
						#If same serial no found then prepare body to register on server
						if sr_no==sr_no_record['serialNo']:
							for single_serial_no in all_serial_no_response[sr_no]:
								obj={}
								obj['serialNo']=single_serial_no #child serial no
								obj['model']=sr_no_record["model"]
								obj['custName']=sr_no_record["custName"]
								obj['dcNo']=sr_no_record["dcNo"]
								obj['dcDate']=sr_no_record["dcDate"]
								obj['mastCode']="0"
								obj['subModelType']="0"
								body.append(obj)
			
								doc = frappe.new_doc("Sub Serial No")
								doc.parent_serial_no = sr_no #main serial no
								doc.item_code = sr_no_record["item_code"]
								doc.model = sr_no_record["model"]
								doc.customer_name = sr_no_record["custName"]
								doc.dc = sr_no_record["dcNo"]
								doc.dcdate = sr_no_record["dcDate"]
								doc.custom_marked_in_avdm = 0
								doc.insert(ignore_permissions=True)

			#Create body and pass in same way as main serial no
			cunk_size = 100
			body_send = []
			record_found = False

			for index, record in enumerate(body):
				body_send.append(record)
				if index%cunk_size==0:
					reply['chunk_send_{}'.format(str(index))]="Cunk Send"
					# errorLog(key_body_process,str(body_send)) #Comment
					errorLog('Sub-serial-no',str(body_send))
					record_found = True
					body_send = []

			if len(body_send)!=0:
				record_found = True
				# errorLog(key_body_process,str(body_send))#Comment
				errorLog("Sub-serial-no",str(body_send))
			#If any record is found then 5 min cron set on
			if record_found:
				query = "UPDATE `tabScheduled Job Type` SET `stopped`=0 WHERE `method` = '{}'".format('mantra_dev.backend_code.avdm.process_one_record')
				records = frappe.db.sql(query,as_dict=1)

    
			#Delete serial number which is process
			for err_name in list_body_to_process:
				query = "DELETE FROM `tabError Log` WHERE `name`='{}'".format(err_name['name'])
				records_deleted = frappe.db.sql(query,as_dict=1)

		else:
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="EVDM-sub serial request not process",
				message="fetch_sub_serial_no_records <br>{}<br>{}".format(mssage,str(reply))
			)

	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		mssage = str(traceback.format_exc())
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="EVDM-sub serial not process due to issue",
			message="avdm.py - process_one_record <br>{}<br>{}".format(mssage,str(reply))
		)


@frappe.whitelist(allow_guest=True)
def recoursion_all_serial_no(body_pass):
	# pass_string = "[{\"SerialNo\":\"9346518\",\"Model\":\"BionicFP6\",\"Consume\":[{\"SerialNo\":\"9182844\",\"Model\":\"MFS100V2\",\"Consume\":[]},{\"SerialNo\":\"9255333\",\"Model\":\"BioNICF6\",\"Consume\":[]}]},{\"SerialNo\":\"9346518\",\"Model\":\"BionicFP6\",\"Consume\":[{\"SerialNo\":\"9182844\",\"Model\":\"MFS100V2\",\"Consume\":[]},{\"SerialNo\":\"9255333\",\"Model\":\"BioNICF6\",\"Consume\":[{\"SerialNo\":\"9182844-1\",\"Model\":\"MFS100V2\",\"Consume\":[]},{\"SerialNo\":\"9255333-2\",\"Model\":\"BioNICF6\",\"Consume\":[]}]}]},{\"SerialNo\":\"9401893\",\"Model\":\"BioNIC8-W\",\"Consume\":[{\"SerialNo\":\"9175427\",\"Model\":\"MFS100V2\",\"Consume\":[{\"SerialNo\":\"22222\",\"Model\":\"MF2222\",\"Consume\":[]}]}]}]"
	# body_pass = ast.literal_eval(pass_string)
	
	final_data = {}
	for rec in body_pass:
		final_data[rec['SerialNo']] = process_all_level_serial_no(device=rec,data=[])

	return final_data

def process_all_level_serial_no(device, data):
    
    for sub_device in device.get("Consume", []):
        data.append(sub_device["SerialNo"])
        process_all_level_serial_no(sub_device,data)

    return data


@frappe.whitelist(allow_guest=True)
def update_serial_no_records(limit):

	query = "SELECT error from `tabError Log` WHERE method='{}' LIMIT {}".format(key_serial_no,limit)
	serial_no_list = frappe.db.sql(query)
 
	if len(serial_no_list)==0:
		return "No serial no to update"
 
	flat_list = [r[0] for r in serial_no_list]
	flat_list2 = tuple(flat_list)
	
	query_delete=''
	query_update=''
 
	try:
		query_update = "UPDATE `tabSerial No` SET `custom_marked_in_avdm`=1 WHERE `name` IN {}".format(flat_list2)
  
		query_update = query_update.replace("',)","')")
  
		serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
  
		query_delete = "DELETE FROM `tabError Log` WHERE `method`='{}' AND `error` IN {}".format(key_serial_no,flat_list2)
		query_delete = query_delete.replace("',)","')")
		delete = frappe.db.sql(query_delete,as_dict=1)
  
		return "Delete done"
	except Exception as e:
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Serial no not update bulk",
			message="Line 611 avdm.py <br>{} <br>{} <br>{} <br>{}".format(str(e),str(serial_no_list),query_update,query_delete)
		)
 
	return serial_no_list

@frappe.whitelist(allow_guest=True)
def update_delivery_note_records():

	query = "SELECT error from `tabError Log` WHERE method='{}' LIMIT 1000".format(key_dc_no)
	serial_no_list = frappe.db.sql(query)
	if len(serial_no_list)==0:
		return "No serial no to update"
 
 
	flat_list = [r[0] for r in serial_no_list]
	flat_list2 = tuple(flat_list)
  
	try:
		query = "UPDATE `tabDelivery Note` SET `custom_marked_in_avdm`=1 WHERE `name` IN {}".format(flat_list2)
		query = query.replace("',)","')")

		serial_no_list_update = frappe.db.sql(query,as_dict=1)
  
		query_delete = "DELETE FROM `tabError Log` WHERE `method`='{}' AND `error` IN {}".format(key_dc_no,flat_list2)
		query_delete = query_delete.replace("',)","')")
		delete = frappe.db.sql(query_delete,as_dict=1)
  
		return "Delete done"
	except Exception as e:
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Delivery no not update bulk",
			message="Line 283 avdm.py <br>{} <br>{}".format(str(e),str(serial_no_list))
		)
 
	return serial_no_list























@frappe.whitelist(allow_guest=True)
def update_item_code(item_code,avdm_code):


	# query = """
	# 	SELECT 
	# 		dni.item_code,
	# 		SUM(dni.qty) AS total_qty
	# 	FROM 
	# 		`tabDelivery Note Item` dni
	# 	JOIN 
	# 		`tabDelivery Note` dn ON dni.parent = dn.name
	# 	WHERE
	# 		dn.docstatus = 1
	# 		AND dn.is_return = 0
	# 		AND dni.custom_abdm_enable = 1
	# 		AND dn.posting_date BETWEEN '{}' AND '{}'
	# 		AND dni.item_code IN ('P0322','P0323','P0704','P0688','P0703','P1541','P1539','P2296','P2349','P2460','P0091','P0308','P0310','P0705','P0309','P0793','P0858','P1523','P1524','P1961','P1970','P1557','P1580','P1581','P1573','P2254','P2217','P2269','P2275')
	# 	GROUP BY 
	# 		dni.item_code
	# """.format('2025-01-11', '2025-02-14')
	# list_body_to_process = frappe.db.sql(query,as_dict=1)
	# return list_body_to_process
 


	query = """
		SELECT 
			dni.parent AS delivery_note,
			dni.item_code,
			SUM(dni.qty) AS total_qty
		FROM 
			`tabDelivery Note Item` dni
		JOIN 
			`tabDelivery Note` dn ON dni.parent = dn.name
		WHERE
			dni.custom_reference_model_no = '{}'
			AND dni.item_code = '{}'
	""".format(avdm_code,item_code)
	list_body_to_process = frappe.db.sql(query,as_dict=1)
	# return len(list_body_to_process)
	
	update_query = """
		UPDATE `tabDelivery Note Item` dni
		JOIN `tabDelivery Note` dn ON dni.parent = dn.name
		SET dni.custom_reference_model_no = '{}'
		WHERE dni.item_code = '{}'
 	""".format(avdm_code,item_code)
	list_body_to_process_update = frappe.db.sql(update_query,as_dict=1)
	
 
	if len(list_body_to_process)!=0:
		return list_body_to_process[0]
 
	return len(list_body_to_process)


@frappe.whitelist(allow_guest=True)
def process_body_manually():
	reply= {}

	string6 = """[{'mastCode': '0', 'serialNo': '7154876', 'custName': 'SANDEEP RANA', 'dcNo': 'MAN/FG/IN/00160', 'dcDate': '2025-01-11T16:04:24.723236Z', 'model': '11', 'subModelType': '0'}, {'mastCode': '0', 'serialNo': '7142412', 'custName': 'SANDEEP RANA', 'dcNo': 'MAN/FG/IN/00160', 'dcDate': '2025-01-11T16:04:24.723236Z', 'model': '11', 'subModelType': '0'}]"""
	frappe.enqueue(process_body_manually_background, queue='long', timeout=3600,body=string6)

	string7 = """[{'mastCode': '0', 'serialNo': '8127183', 'custName': 'OKI GENERAL TRADING FZCO', 'dcNo': 'MAN/OUT/24-25/25591', 'dcDate': '2025-01-21T14:19:08.024959Z', 'model': '11', 'subModelType': '0'}, {'mastCode': '0', 'serialNo': '8127227', 'custName': 'OKI GENERAL TRADING FZCO', 'dcNo': 'MAN/OUT/24-25/25591', 'dcDate': '2025-01-21T14:19:08.024959Z', 'model': '11', 'subModelType': '0'}]"""
	frappe.enqueue(process_body_manually_background, queue='long', timeout=3600,body=string7)

	string8 = """[{'mastCode': '0', 'serialNo': '4898645', 'custName': 'MR. DILIP JOSHI', 'dcNo': 'MAN/OUT/24-25/26427', 'dcDate': '2025-02-11T14:48:58.036881Z', 'model': '8', 'subModelType': '0'}]"""
	frappe.enqueue(process_body_manually_background, queue='long', timeout=3600,body=string8)

	string9 = """[{'mastCode': '0', 'serialNo': '3819445', 'custName': 'WELSPUN SPECIALTY SOLUTIONS LTD-Jhagadia ( Guj )', 'dcNo': 'MAN/OUT/24-25/26422', 'dcDate': '2025-02-11T14:06:44.977047Z', 'model': '11', 'subModelType': '0'}, {'mastCode': '0', 'serialNo': '3819889', 'custName': 'WELSPUN SPECIALTY SOLUTIONS LTD-Jhagadia ( Guj )', 'dcNo': 'MAN/OUT/24-25/26422', 'dcDate': '2025-02-11T14:06:44.977047Z', 'model': '11', 'subModelType': '0'}, {'mastCode': '0', 'serialNo': '3199827', 'custName': 'MR. DILIP JOSHI', 'dcNo': 'MAN/OUT/24-25/26406', 'dcDate': '2025-02-11T10:25:54.950157Z', 'model': '11', 'subModelType': '0'}]"""
	frappe.enqueue(process_body_manually_background, queue='long', timeout=3600,body=string9)

	return True

@frappe.whitelist(allow_guest=True)
def process_body_manually_background(body):

	reply= {}
	try:

		creating_url = "https://erptoavdm.aadhaardevice.com/ErptoAVDM"

		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 1".format(key_token)
		token = frappe.db.sql(query,as_dict=1)

		if len(token)==0:
			generate_token()
			return "Token not found"

		headers = {
			"accept": "application/json",
			"Authorization": f"Bearer {token[0]['error']}"
		}
	
		body_pass = ast.literal_eval(body)
		process_dc_of_serial={}
		body_pass_avdm = []
		for s_no_data in body_pass:
			process_dc_of_serial[s_no_data['serialNo']]=s_no_data['dcNo']
			s_no_data['dcDate'] = date_convert(s_no_data['dcDate'])
			if int(s_no_data['model']) != 13:
				body_pass_avdm.append(s_no_data)
			

		if len(body_pass_avdm)==0:
			reply['request_url']="No serial no match"
			return reply


		reply['request_url']=creating_url
		reply['request_header']=headers
		reply['request_body']=body_pass_avdm
		

		response1 = requests.post(creating_url, headers=headers, json=body_pass_avdm)
		reply['resposne_status_code']=response1.status_code
		

		dc_response_content = response1.content
		if isinstance(dc_response_content, bytes):
			dc_response_content = dc_response_content.decode('utf-8')
		reply['resposne_contennt']=dc_response_content

		if response1.status_code==200:

			#Get all serial number response in this.
			dc_response_json = json.loads(dc_response_content)
			reply['response']=dc_response_json
			
			if dc_response_json:
				process_dc_no = []
	
				error_searial_no = []
				for i in dc_response_json:
					if int(i['errorCode'])==0:
						errorLog(key_serial_no,str(i['devicesr']))
						if process_dc_of_serial[i['devicesr']] not in delivery_note_number_proccess:
							process_dc_no.append(process_dc_of_serial[i['devicesr']])
							delivery_note_number_proccess.append(process_dc_of_serial[i['devicesr']])
					else:
						error_searial_no.append(str(i['devicesr']))
						# frappe.enqueue(update_serial_no_field,queue='long',job_name="Update serial no {}".format(i['devicesr']),timeout=100000,serial_no=i['devicesr'])

				for dc_no in process_dc_no:
					errorLog(key_dc_no,str(dc_no))
					# frappe.enqueue(update_delivery_field,queue='long',job_name="Update delivery note {}".format(str(dc_no)),timeout=100000,dc_no=str(dc_no))

				#Get all serial no with error reponse
				if len(error_searial_no)!=0:
					email_serial_no_with_error = []
					for s_no_data in body_pass:
						if str(s_no_data['serialNo']) in error_searial_no:
							email_serial_no_with_error.append(s_no_data)

					if len(email_serial_no_with_error)!=0:
						frappe.sendmail(
							recipients=["ravi.patel@mantratec.com"],
							subject="Serial no with error response",
							message="{}".format(str(email_serial_no_with_error))
						)



			reply['message']="process"
			reply['device_process_list']=delivery_note_number_proccess
		else :
			generate_token()
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="AVDM not process due to issue",
				message="avdm.py - process_one_record <br> {}".format(str(reply))
			)
			reply['message']="Not process"
    
	except Exception as e:
			reply['message']="Exception"
			reply['message_traceback']=str(traceback.format_exc())
			mssage = str(traceback.format_exc())
			errorLog("AVDM_error",mssage)
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="AVDM not process due to issue",
				message="avdm.py - process_one_record <br>{}<br>{}".format(mssage,str(reply))
			)
			
	return reply




def send_serial_no_to_server(body,creating_url,headers):
	return
	reply={}
	try:
		process_dc_of_serial={}
		for s_no_data in body:
			process_dc_of_serial[s_no_data['serialNo']]=s_no_data['dcNo']

		response1 = requests.post(creating_url, headers=headers, json=body)
		if response1.status_code==200:
			
			dc_response_content = response1.content
			if isinstance(dc_response_content, bytes):
				dc_response_content = dc_response_content.decode('utf-8')

			#Get all serial number response in this.
			dc_response_json = json.loads(dc_response_content)
			
			if dc_response_json:
				process_dc_no = []
				for i in dc_response_json:
					if int(i['errorCode'])==0:
						if process_dc_of_serial[i['devicesr']] not in delivery_note_number_proccess:
							process_dc_no.append(process_dc_of_serial[i['devicesr']])
							delivery_note_number_proccess.append(process_dc_of_serial[i['devicesr']])

						frappe.enqueue(update_serial_no_field,queue='long',job_name="Update serial no {}".format(i['devicesr']),timeout=100000,serial_no=i['devicesr'])

				for dc_no in process_dc_no:
					frappe.enqueue(update_delivery_field,queue='long',job_name="Update delivery note {}".format(str(dc_no)),timeout=100000,dc_no=str(dc_no))
		else :
			dc_response_json=response1.status_code
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="AVDM not process due to issue",
				message="Line 168 avdm.py"
			)
		reply['message']="Process"
		return dc_response_json
	except Exception as e:
			reply['message']="Exception"
			reply['message_traceback']=str(traceback.format_exc())
			mssage = str(traceback.format_exc())
			errorLog("AVDM",mssage)
			# if not email_send:
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="AVDM not process due to issue",
				message="Line 181 avdm.py <br>{}".format(mssage)
			)
			# email_send = True
			
	return reply

def update_serial_no_field(serial_no):
	try:
		frappe.db.set_value('Serial No', serial_no, 'custom_marked_in_avdm', 1)
	except Exception as e:
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Serial no not update: {}".format(serial_no),
			message="Line 278 avdm.py <br>{}".format(str(e))
		)
	
	return True
 
def update_delivery_field(dc_no):

	try:
		frappe.db.set_value('Delivery Note', dc_no, 'custom_marked_in_avdm', 1)
	except Exception as e:
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Delivery note not update avdm: {}".format(dc_no),
			message="Line 291 avdm.py <br>{}".format(str(e))
		)
	
	return True