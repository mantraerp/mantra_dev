import frappe
from frappe import _
from frappe.utils import nowdate
import json
import traceback
import requests
from mantra_dev.backend_code.globle import errorLog,errorLogExites


delivery_note_number_proccess = []
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
	email_send = False
 
	errorLog('AVDM',transaction_date,False)
	reply={}
    
	if frappe.db.get_single_value("AVDM Setting", "enable") == 1:
		
		dc_list = frappe.get_all("Delivery Note", filters={"posting_date": transaction_date, "docstatus": 1})
		if len(dc_list)==0:
			reply['message']="no delivery note found"
			return reply

		reply['setting_enable']="yes"
		try:
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

			creating_url = "https://erptoavdm.aadhaardevice.com/ErptoAVDM"
			headers = {
				"accept": "application/json",
				"Authorization": f"Bearer {api_token}"
			}
			body = []

			dc_response_json=''
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
									"mastCode": 0,
									"serialNo": s_no,
									"custName": dc_doc.customer_name,
									"dcNo": dc_doc.name,
									"dcDate": f"{dc_doc.posting_date}T{dc_doc.posting_time}Z",
									"model": i.custom_reference_model_no,
									"subModelType": 0
								}
								body.append(data)

			cunk_size = 25

			body_send = []
			for index, record in enumerate(body):
				body_send.append(record)
				if index%cunk_size==0:
					reply['chunk_send_{}'.format(str(index))]="Cunk Send"
					frappe.enqueue(send_serial_no_to_server,queue='long',job_name="AVDM Process",timeout=100000,body=body,creating_url=creating_url,headers=headers)
					body_send = []

			if len(body_send)!=0:
				frappe.enqueue(send_serial_no_to_server,queue='long',job_name="AVDM Process",timeout=100000,body=body,creating_url=creating_url,headers=headers)

			errorLog('AVDM-End',transaction_date,False)
			return reply

		except Exception as e:
			reply['message']="Exception"
			reply['message_traceback']=str(traceback.format_exc())
			mssage = str(traceback.format_exc())
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com"],
				subject="AVDM not process due to exception",
				message="Line 118 avdm.py <br>{}".format(mssage)
			)
	else:
		reply['message']="AVDM setting is not enable"
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="AVDM settings is not enable",
			message="Line 125 avdm.py"
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
	frappe.db.set_value('Serial No', serial_no, 'custom_marked_in_avdm', 1)
	return True
 
def update_delivery_field(dc_no):
	frappe.db.set_value('Delivery Note', dc_no, 'custom_marked_in_avdm', 1)
	return True