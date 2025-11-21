import frappe # type: ignore
from frappe import _ # type: ignore
from frappe.utils import nowdate,today,add_months,add_days # type: ignore
import json
import traceback
import requests # type: ignore
from mantra.backend_code.globle import errorLog,get_app_name,create_todo,send_error_message_to_developer # type: ignore
import ast
from requests.auth import HTTPBasicAuth # type: ignore
from datetime import datetime, timezone

from mantra_dev.backend_code.serialno import serial_no_scheduled,process_dc_api # type: ignore
from frappe.utils.background_jobs import get_jobs # type: ignore



delivery_note_number_proccess = []
key_token = "TOKENAVDM"
key_token_pratham = "TOKENAVDMPRATHAM"

key_body_process = "BODYPROCESSAVDM"
key_serial_no = "SERIALNOAVDM"
key_dc_no = "DCNOAVDM"

print_log = False


#Main serial number to add in list to find its sub serial number
key_sub_serial_no = "SUBSERIALNO"
key_sub_item_code_error_find = "ERRORSRITEMCODENOTFOUND"
key_sub_item_code_model_error_find = "ERRORSRIMODELNOTFOUND"
# When any sr. registration get error response. Not clear from system.
key_sr_register_error_find = "ERRORSRSRREGISTRATION"
# This is to handle one day one time check sub serial no
key_subsr_process = "PROCESSSUBSR"
#Process once for sub serial number register on evdm
key_subsr_try_register = "REGISUBSR"

# email_send = False
evdm_url = "https://erptoavdm.aadhaardevice.com"
pratham_url = "http://prathamapi.mantratecapp.com"

@frappe.whitelist(allow_guest=True)
def login_to_avdm_scheduled():

	if not get_app_name()=="mantra":
		return

	# return get_app_name()
	frappe.enqueue(login_to_avdm, queue='long', timeout=3600,transaction_date=nowdate())
	one_day_old = add_days(nowdate(), -1)
	frappe.enqueue(login_to_avdm, queue='long', timeout=3600,transaction_date=one_day_old)

	# frappe.enqueue(serial_no_scheduled, queue='long', timeout=3600)

	return True  

# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.avdm.process_to_avdm_for_date?transaction_date=2025-06-02

@frappe.whitelist(allow_guest=True)
def process_to_avdm_for_date(transaction_date):
	return login_to_avdm(transaction_date)

@frappe.whitelist()
def login_to_avdm(transaction_date):
	
	#To create ToDo list
	todo_description = "EVDM Process {}".format(str(transaction_date))
	allocated_to="ravi.patel@mantratec.com"
	# frappe.enqueue(create_todo, queue='long', timeout=600, description=todo_description,allocated_to=allocated_to,date=frappe.utils.nowdate(),status='Open',priority='Low',reference_type='',reference_name='')

	delivery_note_number_proccess = [] #reset globle variable

	errorLog('AVDM-Start',transaction_date,False)
	reply={}

	if frappe.db.get_single_value("AVDM Setting", "enable") == 1:
		# dc_list = frappe.get_all("Delivery Note", filters={"posting_date": transaction_date, "docstatus": 1, "is_return": 0})
		
		start_datetime = f"{transaction_date} 00:00:00.000000"
		end_datetime = f"{transaction_date} 23:59:59.000000"

		dc_list = frappe.get_all(
			"Delivery Note",
			filters={
				"modified": ["between", [start_datetime, end_datetime]],
				"docstatus": 1,
				"is_return": 0,
				"custom_marked_in_avdm": 0
			},
			fields=["name", "modified"]
		)

		reply["Total DC"]=len(dc_list)


		if len(dc_list)==0:
			reply['message']="no delivery note found"
			errorLog('AVDM-End',transaction_date,False)
			return reply

		try:
			query = "DELETE FROM `tabError Log` WHERE `method` IN ('{}','{}','{}','{}')".format(key_subsr_process,key_sub_item_code_error_find,key_sub_item_code_model_error_find,key_subsr_try_register)
			records_deleted = frappe.db.sql(query,as_dict=1)

			generate_token()
			generate_token_pratham()
			process_dc_list(dc_list)
			frappe.enqueue(todays_proccess_dc_mail, job_name='Mail',queue='long', timeout=3600,dc_list=dc_list,transaction_date=transaction_date)

			errorLog('AVDM-End',transaction_date,False)
			return reply

		except Exception as e:
			reply['message']="Exception"
			reply['message_traceback']=str(traceback.format_exc())
			mssage = str(traceback.format_exc())
			send_error_message_to_developer("AVDM not process due to exception","avdm.py - login_to_avdm <br>{}".format(mssage))
	else:
		reply['message']="AVDM setting is not enable"
		send_error_message_to_developer("AVDM not process due to exception","avdm.py - login_to_avdm <br>{}".format(mssage))
		
	return reply   


@frappe.whitelist()
def todays_proccess_dc_mail(dc_list,transaction_date):
	
	if not dc_list:
		return "No items found with ABDM enabled."
	
	html_table = f"""
	<h3>DC process count for : {transaction_date}</h3>
	<table border="1" cellspacing="0" cellpadding="5">
	<tr>
	<th>DC No</th>
	</tr>
	"""
	for item in dc_list:
		html_table += f"""
		<tr>
		<td>{item.name}</td>
		</tr>
		"""
	html_table += "</table>"
	
	recipients = ["ravi.patel@mantratec.com"]
	subject = f"{transaction_date} Process DC : {len(dc_list)}"
	message = f"""
		<p>Here is the list of DC process:</p>
		{html_table}
		<br>
		"""
	
	frappe.sendmail(
		recipients=recipients,
		subject=subject,
		message=message
	)

	return f"Email sent successfully to {', '.join(recipients)}"







# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.avdm.login_to_avdm_test?transaction_date=2025-11-13


@frappe.whitelist(allow_guest=True)
def login_to_avdm_test(transaction_date):
	
	#To create ToDo list
	reply={}
	start_datetime = f"{transaction_date} 00:00:00.000000"
	end_datetime = f"{transaction_date} 23:59:59.000000"

	dc_list = frappe.get_all(
		"Delivery Note",
		filters={
			"modified": ["between", [start_datetime, end_datetime]],
			"docstatus": 1,
			"is_return": 0,
			"custom_marked_in_avdm": 0
		},
		fields=["name", "modified"]
	)

	reply["Total DC"]=len(dc_list)
	reply["Total_Data"]=dc_list

	return reply   




# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.avdm.update_item_month?transaction_date=2025-06-02

@frappe.whitelist(allow_guest=True)
def update_item_month(dc_no,item_code,month):
	
	reply={}
	if frappe.session.user not in ['abhishek.jain@mantratec.com','Administrator','ravi.patel@mantratec.com']:
		reply['message']='User is not allow to perform this action'
		# return reply



	dc_list = frappe.get_all("Delivery Note", filters={"name": dc_no, "docstatus": 1, "is_return": 0})
	if len(dc_list)==0:
		reply['message']="Error : DC is not found or return"
		return reply

	query = "SELECT name FROM `tabWarranty Time Period` WHERE `name` = '{}'".format(month)
	warrenty_record = frappe.db.sql(query, as_dict=True)
	if len(warrenty_record)==0:
		reply['message']="Error : Warrenty time is not match with exting data."
		return reply

	dn = frappe.get_doc("Delivery Note", dc_no)

	found_item = False
	dc_item_name = ''
	for item in dn.items:
		if item_code==item.item_code:
			itemDetail = frappe.get_doc("Item", item.item_code)
			if itemDetail.custom_avdm_enable in [1,True]:
				found_item = True
				query = "UPDATE `tabDelivery Note Item` SET `custom_rd_service_time_period`='{}' WHERE `name` = '{}' AND `parent`='{}'".format(month,item.name,dc_no)
				warrenty_record = frappe.db.sql(query, as_dict=True)

	if not found_item:
		reply['message']="Error : Item code not found in DC"
		return reply
	else:
		frappe.db.commit()


	frappe.enqueue(process_single_dc, job_name='DCProcessing',queue='long', timeout=3600,dc_no=dc_no)

	reply['message']="Sucessfully : Process DC in background. You will get log in EVDM Sync Log."
	return reply






@frappe.whitelist(allow_guest=True)
def process_single_dc(dc_no):
	
	if get_app_name()!="mantra":
		return "Application is not mantra"
	
 
 	#Update serial no in master
	process_dc_api(dc_no)
 
	dc_list = frappe.get_all("Delivery Note", filters={"name": dc_no, "docstatus": 1, "is_return": 0})

	if len(dc_list)!=0:
		generate_token()
		generate_token_pratham()
		process_dc_list(dc_list)
		return f"DC found. Background process start {str(dc_list)}"

	return "DC not found"


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
					
					#To handle if item code previously not having AVDM enable change change it now
					if i.custom_abdm_enable == 0 or i.custom_reference_model_no in ['',None," "]:
						query_item = "SELECT * FROM `tabItem` WHERE `name` = '{}'".format(i.item_code)
						item_detail = frappe.db.sql(query_item,as_dict=1)
						if len(item_detail)!=0:
							if item_detail[0]['custom_avdm_enable'] in [True,1]:
								frappe.log_error(title="AVDM EVDM",message='try to update')
								query = "UPDATE `tabDelivery Note Item` SET `custom_abdm_enable`=1 WHERE `name` = '{}' AND `parent`='{}'".format(i.name,i.parent)
								if item_detail[0]['custom_reference_model_no'] not in [None,'',' ']:
									query = "UPDATE `tabDelivery Note Item` SET `custom_abdm_enable`=1,`custom_reference_model_no`='{}' WHERE `name` = '{}' AND `parent`='{}'".format(item_detail[0]['custom_reference_model_no'],i.name,i.parent)
								frappe.log_error(title="AVDM EVDM query",message=query)

								records = frappe.db.sql(query,as_dict=1)
								i = frappe.get_doc("Delivery Note Item", i.name)





					if i.custom_abdm_enable == 1 and i.custom_reference_model_no:

						sr_list = []
						if i.serial_no:
							sr_no = i.serial_no
							serial_no = sr_no.replace("\n", ",")
							serial_no_list = serial_no.split(",")

							for s_no in serial_no_list:
								sr_list.append( str(s_no))

						bundle_sr_no = process_dc_bundle(dc_doc.name,i.serial_and_batch_bundle)
						for s_no in bundle_sr_no:
							if s_no['serial_no'] not in sr_list:
								if s_no['item_code'] == i.item_code:
									sr_list.append(str(s_no['serial_no']))


						# frappe.log_error(title=f"DC Serial no {dc}",message=str(sr_list))
						#Remove duplicate
						unique_list = []
						seen = set()

						for item in sr_list:
							if item not in seen:
								seen.add(item)
								unique_list.append(item)


						for s_no in unique_list:
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

			cunk_size = 75

			body_send = []
			for index, record in enumerate(body):
				# if index<=50:
				body_send.append(record)
				if index%cunk_size==0:
					reply['chunk_send_{}'.format(str(index))]="Cunk Send"
					errorLog(key_body_process,str(body_send))
					body_send = []

			if len(body_send)!=0:
				errorLog(key_body_process,str(body_send))

			#If any record is found then 5 min cron set on
			if len(body)!=0:
				query = "UPDATE `tabScheduled Job Type` SET `stopped`=0 WHERE `method` = '{}'".format('mantra_dev.backend_code.avdm.process_one_record')
				records = frappe.db.sql(query,as_dict=1)

			return reply

		except Exception as e:
			reply['message']="Exception"
			reply['message_traceback']=str(traceback.format_exc())
			send_error_message_to_developer("AVDM not process due to exception-Delivery note","avdm.py - process_dc_list <br>{}".format(str(traceback.format_exc())))

	else:
		reply['message']="AVDM setting is not enable"
		send_error_message_to_developer("AVDM settings is not enable","avdm.py - process_dc_list")
		
	return reply


def process_dc_bundle(dc_no,sbb_name):
	
	query = """
		SELECT 
			sbbi.serial_no,
			sbb.item_code
		FROM 
			`tabSerial and Batch Bundle` sbb
		JOIN 
			`tabSerial and Batch Entry` sbbi 
			ON sbbi.parent = sbb.name
		WHERE 
			sbb.voucher_type = 'Delivery Note'
			AND sbb.voucher_no = '{}'
			AND sbb.name = '{}'   
		""".format(dc_no,sbb_name)
	list_body_to_process = frappe.db.sql(query,as_dict=1)
	return list_body_to_process





@frappe.whitelist(allow_guest=True)
def process_one_record():

	if not get_app_name()=="mantra":
		query = "UPDATE `tabScheduled Job Type` SET `stopped`=1 WHERE `method` = 'mantra_dev.backend_code.avdm.process_one_record'"
		records = frappe.db.sql(query,as_dict=1)
		return

	##Comment
	# query = "UPDATE `tabScheduled Job Type` SET `stopped`=1 WHERE `method` = 'mantra_dev.backend_code.avdm.process_one_record'".format('mantra_dev.backend_code.avdm.process_one_record')
	# records = frappe.db.sql(query,as_dict=1)

	#Comment
	frappe.enqueue(process_one_record_background, queue='long', timeout=3600)
	return "process start in background"


def get_all_jobs(method_name):
	#Method name same as in python file
	jobs = get_jobs()
	site_name = frappe.local.site
	runnig_jobs = jobs[site_name]
	all_jobs = []
	for job in runnig_jobs:
		if method_name in str(job):
			all_jobs.append(type(job))
	
	return len(all_jobs)



# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.avdm.process_one_record_background
@frappe.whitelist(allow_guest=True)
def process_one_record_background():

	if not get_app_name()=="mantra":
		return

	if get_all_jobs("process_one_record_background")!=0:
		return "Already schedule in loop"

	reply= {}
	try:
		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 20".format(key_body_process)
		list_body_to_process = frappe.db.sql(query,as_dict=1)
		reply["Body process"]=len(list_body_to_process)
	
		# list_body_to_process=[]

		#If all body process then start update serial no in DB
		if len(list_body_to_process)==0:
			reply["going_to_inner"]=len(list_body_to_process)

			#Start fetching sub-serial no
			query = "SELECT error from `tabError Log` WHERE method='{}' LIMIT 1".format(key_sub_serial_no)
			serial_subserial_no_list = frappe.db.sql(query)
			if len(serial_subserial_no_list)!=0:
				return fetch_sub_serial_no_records()

			#Find sub serial number model number and fill it
			query = "SELECT name FROM `tabSub Serial No` WHERE `custom_marked_in_avdm`=0 AND `find_item_model`=0 AND `fail`=0 AND `name` NOT IN	(SELECT error FROM `tabError Log` WHERE `method`='{}') LIMIT 25".format(key_subsr_process)
			list_body_to_process = frappe.db.sql(query,as_dict=1)
			if len(list_body_to_process)!=0:
				return sub_serial_item_code_and_model()

			#Start process sub serial no
			query_update = "SELECT * FROM `tabSub Serial No` WHERE `find_item_model`=1 AND `custom_marked_in_avdm`=0 AND `name` NOT IN (SELECT error FROM `tabError Log` WHERE `method`='{}') LIMIT 1".format(key_subsr_try_register)
			item_sub_serial_no_list = frappe.db.sql(query_update,as_dict=1)
			if len(item_sub_serial_no_list)!=0:
				return prepare_body_to_upload_subsr()

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
			frappe.enqueue(notify_items_not_found_in_erp, queue='long', timeout=3600)
			frappe.enqueue(notify_model_not_found_in_erp, queue='long', timeout=3600)
			frappe.enqueue(notify_fail_sr_registration_in_erp, queue='long', timeout=3600)

			query = "UPDATE `tabScheduled Job Type` SET `stopped`=1 WHERE `method` = 'mantra_dev.backend_code.avdm.process_one_record'"
			dn_no_list = frappe.db.sql(query)


			#Check serial no
			frappe.enqueue(compare_erp_and_avdm_serial_nos, queue='long', timeout=3600)
			return "All task are done cron stop call"

		# Comment
		# frappe.enqueue(update_serial_no_records, queue='long', timeout=3600,limit=200)
		# frappe.enqueue(fetch_sub_serial_no_records, queue='long', timeout=3600)

		#Process for registration
		creating_url = "{}/ErptoAVDM".format(evdm_url)
	
		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 1".format(key_token)
		token = frappe.db.sql(query,as_dict=1)
	
		if len(token)==0:
			generate_token()
			reply['Token_error']="Token not found"
			return reply
	
		headers = {
			"accept": "application/json",
			"Authorization": f"Bearer {token[0]['error']}"
		}
		reply['message']="Going to register serial no body on server key {}".format(key_body_process)
		for process_record in list_body_to_process:
			frappe.enqueue(process_request, queue='long', timeout=3600,process_record=process_record,creating_url=creating_url,headers=headers)

	except Exception as e:
			reply['message']=str(e)
			reply['message_traceback']=str(traceback.format_exc())
			send_error_message_to_developer("Error: AVDM not process due to issue","process_one_record_background <br>{}".format(str(reply)))

	return reply

# def update_error_log_key_name(error_log):
# 	query_update_sub_date = "UPDATE `tabError Log` SET `method`='BODYPROCESSAVDM-NOT' WHERE `name`='{}'".format(error_log['name'])
# 	sr_no_details = frappe.db.sql(query_update_sub_date,as_dict=1)
# 	return True
											


@frappe.whitelist(allow_guest=True)
def process_request_temp(serialNo):
	query_update = "SELECT warranty_expiry_date,amc_expiry_date FROM `tabSerial No` WHERE `name`='{}'".format(serialNo)
	sr_no_details = frappe.db.sql(query_update,as_dict=1)
	return sr_no_details
	if len(sr_no_details)!=0:
		rd_end_date = sr_no_details[0]['amc_expiry_date']
		if rd_end_date not in ["",None," ","None"]:
			return str(sr_no_details[0]['amc_expiry_date'])


@frappe.whitelist(allow_guest=True)
def process_request(process_record,creating_url,headers):

	reply={}
	try:
		body_pass = ast.literal_eval(process_record['error'])
		process_dc_of_serial={}
		body_pass_avdm = []
		body_not_process = []
		for s_no_data in body_pass:
			process_dc_of_serial[s_no_data['serialNo']]=s_no_data['dcNo']
			s_no_data['dcDate'] = date_convert(s_no_data['dcDate'])

			found_exp = False
			#get expire date for serial no
			#rdEndDate = amc_expiry_date
			#SELECT warranty_expiry_date,amc_expiry_date FROM `tabSerial No` WHERE `name`='9408938'
			query_update = "SELECT warranty_expiry_date,amc_expiry_date FROM `tabSerial No` WHERE `name`='{}'".format(s_no_data['serialNo'])
			sr_no_details = frappe.db.sql(query_update,as_dict=1)
			if len(sr_no_details)!=0:
				rd_end_date = sr_no_details[0]['amc_expiry_date']
				if rd_end_date not in ["",None," ","None"]:
					s_no_data['rdEndDate'] = str(sr_no_details[0]['amc_expiry_date'])
					found_exp = True
			else:
				#If serial number not found in main then search it in sub serial number
				query_update = "SELECT warranty_expiry_date,amc_expiry_date FROM `tabSub Serial No` WHERE `name`='{}'".format(s_no_data['serialNo'])
				sr_no_details = frappe.db.sql(query_update,as_dict=1)
				if len(sr_no_details)!=0:
					rd_end_date = sr_no_details[0]['amc_expiry_date']
					if rd_end_date not in ["",None," ","None"]:
						s_no_data['rdEndDate'] = str(sr_no_details[0]['amc_expiry_date'])
						found_exp = True


			if not found_exp:
				# frappe.log_error(title='RDEXPNOTFOUNDNEW',message=str(s_no_data))
				errorLog('RDEXPNOTFOUNDNEW',str(s_no_data).replace("'","''"),True)
				continue

			try:
				if str(s_no_data['model']) != '13':
					body_pass_avdm.append(s_no_data)
			except Exception as e:
				body_not_process.append(s_no_data)

		if len(body_not_process)!=0:
			send_error_message_to_developer("Error Criticle: Serial number not process","{}".format(str(body_not_process)))

		if len(body_pass_avdm)==0:
			#Once process delete record from error log
			query = "DELETE FROM `tabError Log` WHERE `name`='{}'".format(process_record['name'])
			records_deleted = frappe.db.sql(query,as_dict=1)
			reply['request_url']="No serial no match"
			return reply

		reply['request_url']=creating_url
		reply['request_header']=headers
		reply['request_body']=body_pass_avdm

		if print_log:
			frappe.log_error("AVDM Request URL",str(creating_url))
			frappe.log_error("AVDM Request Header",str(headers))
			frappe.log_error("AVDM Request Body",str(body_pass_avdm))

		# reply['request_dump']=body_json
		response1 = requests.post(creating_url, headers=headers, json=body_pass_avdm)
		reply['resposne_status_code']=str(response1.status_code)

		if print_log:
			frappe.log_error("AVDM Response status code",str(response1.status_code))

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
						errorLog(key_serial_no,str(i['devicesr'])) #insert into error log to update tick
						if process_dc_of_serial[i['devicesr']] not in delivery_note_number_proccess:
							process_dc_no.append(process_dc_of_serial[i['devicesr']])
							delivery_note_number_proccess.append(process_dc_of_serial[i['devicesr']])
					else:
						error_searial_no.append(str(i['devicesr']))

				for dc_no in process_dc_no:
					errorLog(key_dc_no,str(dc_no))

				#Get all serial no with error reponse
				if len(error_searial_no)!=0:
					email_serial_no_with_error = []
					for s_no_data in body_pass:
						if str(s_no_data['serialNo']) in error_searial_no:
							# email_serial_no_with_error.append(s_no_data)
							errorLog(key_sr_register_error_find,str(s_no_data))

					# if len(email_serial_no_with_error)!=0:
					# 	frappe.sendmail(
					# 		recipients=["ravi.patel@mantratec.com"],
					# 		subject="Serial no with error response",
					# 		message="{}".format(str(email_serial_no_with_error))
					# 	)
		else:
			dc_response_json = json.loads(dc_response_content)
			reply['response']=dc_response_json
			send_error_message_to_developer("Error: AVDM request process error","{}".format(str(reply)))
		try:
			todo = frappe.get_doc({
					"doctype": "EVDM Sync Log",
					"url": str(reply['request_url']),
					"execute": True,
					"response_status": str(reply['resposne_status_code']),
					"payload": str(reply['request_body']),
					"response": str(reply['response']),
					"call_type": "EVDM Body",
				})
			todo.insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error("Start saving doc",str(e))

	except Exception as e:
		reply['message']=str(e)
		mssage = str(traceback.format_exc())
		reply['message_traceback']=mssage
		send_error_message_to_developer("Error: AVDM not process due to issue","process_request <br>{}".format(str(reply)))

	return reply





@frappe.whitelist()
def fetch_sub_serial_no_records():

	reply={}
	reply["Process_status"]="Serial no sub"
	limit_records = 250
	try:
		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT {}".format(key_sub_serial_no,limit_records)
		list_body_to_process = frappe.db.sql(query,as_dict=1)
		reply["Process_data"]=len(list_body_to_process)

		searil_no_pass = []
		record_to_be_proccess = []		
		# for process_record in list_body_to_process:
		for index, process_record in enumerate(list_body_to_process):      
			body_pass = ast.literal_eval(process_record['error'])  
			record_to_be_proccess.append(body_pass)
			searil_no_pass.append(body_pass['serialNo'])


		if len(searil_no_pass)==0:
			return "No serial number found"

		#Process for sub serial no
		creating_url = "{}/Production/api/Product/GetConsumeSerialNoDetails".format(pratham_url)

		query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 1".format(key_token_pratham)
		token = frappe.db.sql(query,as_dict=1)

		if len(token)==0:
			generate_token_pratham()
			return "Token not found"

		headers = {
			"accept": "application/json",
			"Token": token[0]['error'],
			"DeviceCode": 'A'
		}

		reply['request_url']=creating_url
		reply['request_header']=headers
		reply['request_body']=searil_no_pass  

		response1 = requests.post(creating_url, headers=headers, json=searil_no_pass)
		reply['resposne_status_code']=str(response1.status_code)
		dc_response_content = response1.content
		if isinstance(dc_response_content, bytes):
			dc_response_content = dc_response_content.decode('utf-8')
		reply['resposne_contennt']=dc_response_content

		# return record_to_be_proccess
		if response1.status_code==200:
			#Get all serial number response in this.
			dc_response_json = json.loads(dc_response_content)
			reply['response']=dc_response_json

			if isinstance(dc_response_json, dict):
				if dc_response_json['isSuccess'] in [False,"False",0,"false"]:
					send_error_message_to_developer("Return Sucess is false","fetch_sub_serial_no_records <br>{}".format(str(reply)))
					dc_response_json = []

			if len(dc_response_json)!=0:
				# if dc_response_json['isSuccess'] in [True,"True",1,"true"]:
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
								process_sub_serial_no = single_serial_no.keys()
								for sub_serial_no in process_sub_serial_no:
									# obj={}
									# obj['serialNo']=sub_serial_no #child serial no
									#find model no here
									#item_code = process_sub_serial_no[sub_serial_no]
									# obj['model']=sr_no_record["model"]
									# obj['custName']=sr_no_record["custName"]
									# obj['dcNo']=sr_no_record["dcNo"]
									# obj['dcDate']=sr_no_record["dcDate"]
									# obj['mastCode']="0"
									# obj['subModelType']="0"
									# body.append(obj)

									reply['sub_serial_no']=sub_serial_no
									reply['sr_no']=sr_no
									reply['sr_no_record']=str(sr_no_record)

									try:
										if not frappe.db.exists("Sub Serial No", sub_serial_no):
											doc = frappe.new_doc("Sub Serial No")
											doc.parent_serial_no = str(sr_no)
											doc.serial_no = sub_serial_no
											doc.item_code = str(sr_no_record["item_code"])
											doc.sub_item_code = single_serial_no[sub_serial_no]         
											doc.model = str(sr_no_record["model"])
											doc.sub_model = ""
											doc.customer_name = str(sr_no_record["custName"])
											doc.dc = str(sr_no_record["dcNo"])
											doc.dcdate = str(sr_no_record["dcDate"])
											doc.custom_marked_in_avdm = False
											doc.find_item_mode = False
											doc.insert(ignore_permissions=True)
											frappe.enqueue(update_sub_serial_no_dates, queue='short', timeout=3600,main_serial_no=str(sr_no),sub_serial_no=sub_serial_no)      
										else:
											query_update_sub_date = "UPDATE `tabSub Serial No` SET `fail`=0,`remark`='' WHERE `name`='{}'".format(sub_serial_no)
											sr_no_details = frappe.db.sql(query_update_sub_date,as_dict=1)
											frappe.enqueue(update_sub_serial_no_dates, queue='short', timeout=3600,main_serial_no=str(sr_no),sub_serial_no=sub_serial_no)      

											
									except Exception as e:
										send_error_message_to_developer("Error: EVDM-sub-serial-error","fetch_sub_serial_no_records <br>{}<br>{}<br>{}".format(str(reply),str(e),str(str(traceback.format_exc()))))

				# else:
				# 	frappe.sendmail(
				# 		recipients=["ravi.patel@mantratec.com"],
				# 		subject="Not Sucess: EVDM serial detail not found",
				# 		message="fetch_sub_serial_no_records <br><br>{}".format(str(reply))
				# 	)
			#Delete serial number which is process
			for err_name in list_body_to_process:
				query = "DELETE FROM `tabError Log` WHERE `name`='{}'".format(err_name['name'])
				records_deleted = frappe.db.sql(query,as_dict=1)

			return "Body process sucessfully {}. Key name : SUBSERIALNO".format(limit_records)
		else:
			dc_response_json = json.loads(dc_response_content)
			reply['response']=dc_response_json
			send_error_message_to_developer("Error: EVDM-sub serial request not process","fetch_sub_serial_no_records <br>{}".format(str(reply)))

		# todo = frappe.get_doc({
		# 	"doctype": "EVDM Sync Log",
		# 	"url": str(reply['request_url']),
		# 	"execute": True,
		# 	"response_status": str(reply['resposne_status_code']),
		# 	"payload": str(reply['request_body']),
		# 	"response": str(reply['response']),
		# 	"call_type": "Sub-serial no body",
		# })
		# todo.insert(ignore_permissions=True)

	except Exception as e:
		reply['message']=str(e)
		mssage = str(traceback.format_exc())
		reply['message_traceback']=mssage
		send_error_message_to_developer("Error: EVDM-sub serial not process due to issue exception","fetch_sub_serial_no_records <br>{}<br>{}".format(mssage,str(reply)))

	return reply

def update_sub_serial_no_dates(main_serial_no,sub_serial_no):
    
	# frappe.log_error(title=f"Sub sr {main_serial_no} - {sub_serial_no}",message='')
	query_update = "SELECT warranty_expiry_date,amc_expiry_date,item_code FROM `tabSerial No` WHERE `name`='{}'".format(main_serial_no)
	sr_no_details = frappe.db.sql(query_update,as_dict=1)

	if len(sr_no_details)!=0:
		amc = sr_no_details[0]['amc_expiry_date']
		warranty = sr_no_details[0]['warranty_expiry_date']
		if amc not in ['None',None,""]:
			query_update_sub_date = "UPDATE `tabSub Serial No` SET `amc_expiry_date`='{}' WHERE `name`='{}'".format(amc,sub_serial_no)
			sr_no_details = frappe.db.sql(query_update_sub_date,as_dict=1)
			query_update_sub_date2 = "UPDATE `tabSerial No` SET `amc_expiry_date`='{}' WHERE `name`='{}'".format(amc,sub_serial_no)
			sr_no_details = frappe.db.sql(query_update_sub_date2,as_dict=1)
		else:
			frappe.enqueue(find_subserialno_amc_when_main_sr_no_having_date, queue='short', timeout=3600,main_serial_no=str(main_serial_no),sub_serial_no=sub_serial_no)      

		if warranty not in ['None',None,""]:
			query_update_sub_date = "UPDATE `tabSub Serial No` SET `warranty_expiry_date`='{}' WHERE `name`='{}'".format(warranty,sub_serial_no)
			sr_no_details = frappe.db.sql(query_update_sub_date,as_dict=1)
			query_update_sub_date2 = "UPDATE `tabSerial No` SET `warranty_expiry_date`='{}' WHERE `name`='{}'".format(warranty,sub_serial_no)
			sr_no_details = frappe.db.sql(query_update_sub_date2,as_dict=1)
		else:
			frappe.enqueue(find_subserialno_waranty_when_main_sr_no_having_date, queue='short', timeout=3600,main_serial_no=str(main_serial_no),sub_serial_no=sub_serial_no)      


		# query_update_sub_date = "UPDATE `tabSub Serial No` SET `amc_expiry_date`='{}',`warranty_expiry_date`='{}' WHERE `name`='{}'".format(sr_no_details[0]['amc_expiry_date'],sr_no_details[0]['warranty_expiry_date'],sub_serial_no)
		# sr_no_details = frappe.db.sql(query_update_sub_date,as_dict=1)
	return True

@frappe.whitelist(allow_guest=True)
def find_subserialno_amc_when_main_sr_no_having_date(main_serial_no,sub_serial_no):
	
	try:
		query_update_main = "SELECT warranty_expiry_date,amc_expiry_date,item_code FROM `tabSerial No` WHERE `name`='{}'".format(main_serial_no)
		main_sr_no_details = frappe.db.sql(query_update_main,as_dict=1)

		query_update_sub = "SELECT warranty_expiry_date,amc_expiry_date,item_code,sub_item_code,dc FROM `tabSub Serial No` WHERE `name`='{}'".format(sub_serial_no)
		sub_sr_no_details = frappe.db.sql(query_update_sub,as_dict=1)    

		if len(main_sr_no_details)==0:
			return "Main serial no not found"

		if len(sub_sr_no_details)==0:
			return "Sub serial no not found"    
		
		item_detail = frappe.get_doc("Item", sub_sr_no_details[0]['sub_item_code'])
		if item_detail.custom_submodel_avdm_enable in [False,0]:
			return "Sub model no process is not enable"

		query_list_dc = "SELECT name,posting_date FROM `tabDelivery Note` WHERE `name`='{}'".format(sub_sr_no_details[0]['dc'])
		dc_list = frappe.db.sql(query_list_dc,as_dict=1)    

		if len(dc_list)==0:
			return "Delivery note not found"
		
		query = "SELECT sbb.name as bundle_name,sbb.voucher_type, sbb.item_code, sbb.voucher_no,sbb.type_of_transaction FROM `tabSerial and Batch Entry` sbbi JOIN `tabSerial and Batch Bundle` sbb ON sbbi.parent = sbb.name WHERE sbb.docstatus != 2 AND sbb.voucher_type='Delivery Note' AND sbb.voucher_no='{}' AND sbbi.serial_no = '{}'".format(sub_sr_no_details[0]['dc'],main_serial_no)
		batch_bundle = frappe.db.sql(query,as_dict=True)    
		if len(batch_bundle)==0:
			return "Serial batch no not found"

		query_list_dc_item = "SELECT * FROM `tabDelivery Note Item` WHERE `serial_and_batch_bundle`='{}'".format(batch_bundle[0]['bundle_name'])
		dc_item_list = frappe.db.sql(query_list_dc_item,as_dict=1)

		if len(dc_item_list)==0:
			return "Serial batch no not found"
		
		warranty = dc_item_list[0]['custom_warranty_time_periodin_months']
		month_to_add = 15
		new_warranty_date = add_months(dc_list[0]['posting_date'], month_to_add)
		if warranty not in ['None',None,"","Not Applicable","No Warranty"]:
			first_obj = str(dc_item_list[0]['custom_warranty_time_periodin_months']).split(" ")[0]
			first_obj = first_obj.replace(' ', ' ')
			first_obj = first_obj.replace('\n', ' ')
			first_obj = first_obj.replace('\r', ' ')
			first_obj = str(first_obj).split(" ")[0]

			if str(first_obj).lower() not in ["no","not","","0",None]:
				month_to_add = int(first_obj)
				if month_to_add==12:
					month_to_add = 15
				new_warranty_date = add_months(dc_list[0]['posting_date'], month_to_add)

		query_update_sub_date = "UPDATE `tabSub Serial No` SET `amc_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,sub_serial_no)
		sr_no_details = frappe.db.sql(query_update_sub_date,as_dict=1)    
	
		query_update_sub_date2 = "UPDATE `tabSerial No` SET `amc_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,sub_serial_no)
		sr_no_details = frappe.db.sql(query_update_sub_date2,as_dict=1) 
 
	except Exception as e:
		frappe.log_error(title=f"Issue in find_subserialno_amc_when_main_sr_no_having_date", message= str(e))
		return f"eception: {str(e)}\n{str(traceback.format_exc())}"
 
 
	return "Process done"

def find_subserialno_waranty_when_main_sr_no_having_date(main_serial_no,sub_serial_no):

	try:
		query_update_main = "SELECT warranty_expiry_date,amc_expiry_date,item_code FROM `tabSerial No` WHERE `name`='{}'".format(main_serial_no)
		main_sr_no_details = frappe.db.sql(query_update_main,as_dict=1)

		query_update_sub = "SELECT warranty_expiry_date,amc_expiry_date,item_code,sub_item_code,dc FROM `tabSub Serial No` WHERE `name`='{}'".format(sub_serial_no)
		sub_sr_no_details = frappe.db.sql(query_update_sub,as_dict=1)    

		if len(main_sr_no_details)==0:
			return "Main serial no not found"

		if len(sub_sr_no_details)==0:
			return "Sub serial no not found"    
		
		item_detail = frappe.get_doc("Item", sub_sr_no_details[0]['sub_item_code'])
		if item_detail.custom_submodel_avdm_enable in [False,0]:
			return "Sub model no process is not enable"


		query_list_dc = "SELECT name,posting_date FROM `tabDelivery Note` WHERE `name`='{}'".format(sub_sr_no_details[0]['dc'])
		dc_list = frappe.db.sql(query_list_dc,as_dict=1)    

		if len(dc_list)==0:
			return "Delivery note not found"
		
		query = "SELECT sbb.name as bundle_name,sbb.voucher_type, sbb.item_code, sbb.voucher_no,sbb.type_of_transaction FROM `tabSerial and Batch Entry` sbbi JOIN `tabSerial and Batch Bundle` sbb ON sbbi.parent = sbb.name WHERE sbb.docstatus != 2 AND sbb.voucher_type='Delivery Note' AND sbb.voucher_no='{}' AND sbbi.serial_no = '{}'".format(sub_sr_no_details[0]['dc'],main_serial_no)
		batch_bundle = frappe.db.sql(query,as_dict=True)    
		if len(batch_bundle)==0:
			return "Serial batch no not found"

		query_list_dc_item = "SELECT * FROM `tabDelivery Note Item` WHERE `serial_and_batch_bundle`='{}'".format(batch_bundle[0]['bundle_name'])
		dc_item_list = frappe.db.sql(query_list_dc_item,as_dict=1)

		if len(dc_item_list)==0:
			return "Serial batch no not found"
		
		warranty = dc_item_list[0]['custom_rd_service_time_period']
		month_to_add = 15
		new_warranty_date = add_months(dc_list[0]['posting_date'], month_to_add)
		if warranty not in ['None',None,"","Not Applicable","No Warranty"]:
			first_obj = str(dc_item_list[0]['custom_rd_service_time_period']).split(" ")[0]
			first_obj = first_obj.replace(' ', ' ')
			first_obj = first_obj.replace('\n', ' ')
			first_obj = first_obj.replace('\r', ' ')
			first_obj = str(first_obj).split(" ")[0]

			if str(first_obj).lower() not in ["no","not","","0",None]:
				month_to_add = int(first_obj)
				new_warranty_date = add_months(dc_list[0]['posting_date'], month_to_add)

		query_update_sub_date = "UPDATE `tabSub Serial No` SET `warranty_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,sub_serial_no)
		sr_no_details = frappe.db.sql(query_update_sub_date,as_dict=1)    

		query_update_sub_date2 = "UPDATE `tabSerial No` SET `warranty_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,sub_serial_no)
		sr_no_details = frappe.db.sql(query_update_sub_date2,as_dict=1)

	except Exception as e:
		frappe.log_error(title=f"Issue in find_subserialno_waranty_when_main_sr_no_having_date", message= str(e))
		return f"eception: {str(e)}\n{str(traceback.format_exc())}"
 
 
	return "Process done"


def recoursion_all_serial_no(body_pass):
	
	final_data = {}
	for rec in body_pass:
		final_data[rec['SerialNo']] = process_all_level_serial_no(device=rec,data=[])

	return final_data

def process_all_level_serial_no(device, data):
	
	for sub_device in device.get("Consume", []):
		objDict={}
		objDict[sub_device["SerialNo"]]=sub_device["OdooId"]
		data.append(objDict)
		
		process_all_level_serial_no(sub_device,data)

	return data




##############################################################
#Check all sub serial number item code and model number code
@frappe.whitelist(allow_guest=True)
def sub_serial_item_code_and_model():

	reply={}
	reply["Process_status"]="Serial no sub model and item code finding"
	try:
		query = "SELECT name FROM `tabSub Serial No` WHERE `custom_marked_in_avdm`=0 AND `find_item_model`=0 AND `fail`=0 AND `name` NOT IN	(SELECT error FROM `tabError Log` WHERE `method`='{}') LIMIT 25".format(key_subsr_process)
		# query = "SELECT name FROM `tabSub Serial No` WHERE `custom_marked_in_avdm`=0 AND `find_item_model`=0 AND `fail`=0 LIMIT 25"
		list_body_to_process = frappe.db.sql(query,as_dict=1)
		# frappe.log_error(title='Total Remain',message=len(list_body_to_process))
		reply["Process_data"]=len(list_body_to_process)
		for process_record in list_body_to_process:
			frappe.enqueue(sub_serial_item_code_and_model_adding, queue='long', timeout=3600,serial_no=process_record['name'])      
			frappe.enqueue(sub_serial_item_code_and_model_checking, queue='long', timeout=3600,doc_name=process_record['name'])

	except Exception as e:
		reply['message']=str(e)
		mssage = str(traceback.format_exc())
		reply['message_traceback']=mssage

	return reply

def sub_serial_item_code_and_model_adding(serial_no):
	errorLog(key_subsr_process,str(serial_no))
	return True

@frappe.whitelist(allow_guest=True)
def sub_serial_item_code_and_model_checking(doc_name):

	query = "SELECT sub_item_code,name from `tabSub Serial No` WHERE `custom_marked_in_avdm`=0 AND `find_item_model`=0 AND `name`='{}'".format(doc_name)
	list_serial_no = frappe.db.sql(query,as_dict=1)
	# frappe.log_error(title='AVDMSERIALNOPROCESS',message=str(list_serial_no))

	for serial_no_record in list_serial_no:
		query = "SELECT custom_reference_submodel_no,name from `tabItem` WHERE `name`='{}'".format(serial_no_record['sub_item_code'])
		list_item = frappe.db.sql(query,as_dict=1)

		if len(list_item)==0:
			query_update = "UPDATE `tabSub Serial No` SET `remark`='{}',`fail`=1 WHERE `name`='{}'".format(key_sub_item_code_error_find,doc_name)
			update_item_detail = frappe.db.sql(query_update,as_dict=1)
			return "Item code not found"
		else:
			for item in list_item:
				# if item['custom_submodel_avdm_enable']:
				if item['custom_reference_submodel_no'] not in ['',None," "]:
					query_update = "UPDATE `tabSub Serial No` SET `sub_model`='{}', `find_item_model`=1, `remark`='' WHERE `name`='{}'".format(str(item['custom_reference_submodel_no']),doc_name)
					update_item_detail = frappe.db.sql(query_update,as_dict=1)
					return "Item detail update"
				else:
					query_update = "UPDATE `tabSub Serial No` SET `remark`='{}',`fail`=1 WHERE `name`='{}'".format(key_sub_item_code_model_error_find,doc_name)
					update_item_detail = frappe.db.sql(query_update,as_dict=1)
					return "Model number not found"
				# else:
				# 		query_update = "UPDATE `tabSub Serial No` SET `find_item_model`=1,`custom_marked_in_avdm`=1 `remark`='SUBCODENOTREGINEVDM' WHERE `name`='{}'".format(str(item['custom_reference_submodel_no']),doc_name)
				# 		update_item_detail = frappe.db.sql(query_update,as_dict=1)
				# 		return "Item detail update"


	return "Process document {}".format(doc_name)
	

def notify_items_not_found_in_erp():

	email_recipients = ["ravi.patel@mantratec.com","abhishek.jain@mantratec.com","sajal.chandrawanshi@mantratec.com"]
	# email_recipients = ["ravi.patel@mantratec.com"]

	try:
		bank_accounts = frappe.get_all(
			"Sub Serial No",
			filters={
				"find_item_model": 0,
				"remark":key_sub_item_code_error_find,
			},
			fields=["name", "sub_item_code","item_code"]
		)

		if not bank_accounts:
			return "No remaining item code found."

		body = "<b>List of item code which is not found in erp:</b><br><br>"
		body += "<b>List of item code which is not found in erp but received from pratham with sub-serial no<br><br>Total : {}</b><br><br>".format(len(bank_accounts))

		body += """<table style="width: 100%;">
			<tbody>
				<tr>
					<td style="width: 30%"><strong>Serial No.</strong></td>
					<td style="width: 30%"><strong>Item Code</strong></td>
					<td style="width: 30%"><strong>Main part item code</strong></td>
				</tr>
			"""

		for row in bank_accounts:
			body += """<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>""".format(row.name, row.sub_item_code,row.item_code)

		body += "</tbody></table>"

		frappe.sendmail(
			recipients=email_recipients,
			subject="Pratham : Item code not found in ERP",
			message=body
		)

	except Exception as e:
		frappe.sendmail(
			recipients=['ravi.patel@mantratec.com'],
			subject="Error while checking Item code for pratham",
			message="{}<br>{}".format(str(e),str(traceback.format_exc())),
		)

	return "Email sent successfully!"

@frappe.whitelist(allow_guest=True)
def notify_model_not_found_in_erp():

	email_recipients = ["ravi.patel@mantratec.com","abhishek.jain@mantratec.com","sajal.chandrawanshi@mantratec.com"]
	# email_recipients = ["ravi.patel@mantratec.com"]

	try:
		bank_accounts = frappe.get_all(
			"Sub Serial No",
			filters={
				"find_item_model": 0,
				"remark":key_sub_item_code_model_error_find,
			},
			fields=["name", "sub_item_code","item_code"]
		)

		if not bank_accounts:
			return "No remaining item code found."

		body = "<b>List of Item code model number which is not found in pratham but set in ERP:</b><br><br>"
		body += "<b>Total : {}</b><br><br>".format(len(bank_accounts))

		body += """<table style="width: 100%;">
			<tbody>
				<tr>
					<td style="width: 30%"><strong>Serial No.</strong></td>
					<td style="width: 30%"><strong>Item Code</strong></td>
					<td style="width: 30%"><strong>Main part item code</strong></td>
				</tr>
			"""
		for row in bank_accounts:
			body += """<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>""".format(row.name, row.sub_item_code,row.item_code)

		body += "</tbody></table>"

		frappe.sendmail(
			recipients=email_recipients,
			subject="Pratham : Item code model number not found in ERP",
			message=body
		)

	except Exception as e:
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com","abhishek.jain@mantratec.com","sajal.chandrawanshi@mantratec.com"],
			subject="Error while checking Item code for pratham",
			message="{}<br>{}".format(str(e),str(traceback.format_exc())),
		)

	return "Email sent successfully!"


def prepare_body_to_upload_subsr():

	query_update = "SELECT * FROM `tabSub Serial No` WHERE `find_item_model`=1 AND `custom_marked_in_avdm`=0 AND `name` NOT IN	(SELECT error FROM `tabError Log` WHERE `method`='{}')".format(key_subsr_try_register)
	item_sub_serial_no_list = frappe.db.sql(query_update,as_dict=1)

	body = []
	for rec in item_sub_serial_no_list:
		data = {
			"mastCode": "0",
			"serialNo": str(rec['name']),
			"custName": str(rec['customer_name']),
			"dcNo": str(rec['dc']),
			"dcDate": str(rec['dcdate']),
			"model": str(rec['sub_model']),
			"subModelType": "0"
		}
		body.append(data)
		errorLog(key_subsr_try_register,str(rec['name']))

	cunk_size = 25

	body_send = []
	for index, record in enumerate(body):
		body_send.append(record)
		if index%cunk_size==0:
			errorLog(key_body_process,str(body_send))
			body_send = []

	if len(body_send)!=0:
		errorLog(key_body_process,str(body_send))

	#If any record is found then 5 min cron set on
	if len(body)!=0:
		query = "UPDATE `tabScheduled Job Type` SET `stopped`=0 WHERE `method` = '{}'".format('mantra_dev.backend_code.avdm.process_one_record')
		records = frappe.db.sql(query,as_dict=1)
		return "Sub serial no body is prepare"


	return "No sub serial no body is found"
	
##############################################################

@frappe.whitelist(allow_guest=True)
def notify_fail_sr_registration_in_erp():

	email_recipients = ["ravi.patel@mantratec.com","abhishek.jain@mantratec.com","sajal.chandrawanshi@mantratec.com"]
	# email_recipients = ["ravi.patel@mantratec.com"]

	try:
	
		query = "SELECT * from `tabError Log` WHERE method='{}'".format(key_sr_register_error_find)
		list_erros_to_process = frappe.db.sql(query,as_dict=1)     
	
		if not list_erros_to_process:
			return "No remaining item code found."

		body = "<b>List of Item code model number which is not found in erp:</b><br><br>"
		body += "<b>Total : {}</b><br><br>".format(len(list_erros_to_process))

		body += """<table style="width: 100%;">
			<tbody>
				<tr>
					<td style="width: 30%"><strong>Serial No.</strong></td>
				</tr>
			"""
		for row in list_erros_to_process:
			body += """<tr><td>{0}</td></tr>""".format(row.error)

		body += "</tbody></table>"

		frappe.sendmail(
			recipients=email_recipients,
			subject="EVDM: Serial number not register",
			message=body
		)

	except Exception as e:
		frappe.sendmail(
			recipients=['ravi.patel@mantratec.com'],
			subject="EVDM Error: Serial number not register",
			message="{}<br>{}".format(str(e),str(traceback.format_exc())),
		)

	return "Email sent successfully!"



#Update serial number tick in DB
@frappe.whitelist(allow_guest=True)
def update_serial_no_records(limit):

	# limit = 5000
	reply={}
	reply["Process_status"]="Serial update process"
	query = "SELECT error from `tabError Log` WHERE method='{}' LIMIT {}".format(key_serial_no,limit)
	serial_no_list = frappe.db.sql(query)
	reply["serial_no_list"]=serial_no_list
	if len(serial_no_list)==0:
		reply["Process_status_sub"]="No serial no to update"
		return reply

	flat_list = [r[0] for r in serial_no_list]
	flat_list2 = tuple(flat_list)
	
	query_delete=''
	query_update=''

	try:
		#Update serial number
		query_update = "UPDATE `tabSerial No` SET `custom_marked_in_avdm`=1 WHERE `name` IN {}".format(flat_list2)
		query_update = query_update.replace("',)","')")
		serial_no_list_update = frappe.db.sql(query_update,as_dict=1)

		#Update serial number if its in sub
		query_update = "UPDATE `tabSub Serial No` SET `custom_marked_in_avdm`=1 WHERE `name` IN {}".format(flat_list2)
		query_update = query_update.replace("',)","')")
		serial_no_list_update = frappe.db.sql(query_update,as_dict=1)

		#Update in So Serial Number Log



		#Delete updated serial number from log
		query_delete = "DELETE FROM `tabError Log` WHERE `method`='{}' AND `error` IN {}".format(key_serial_no,flat_list2)
		query_delete = query_delete.replace("',)","')")
		delete = frappe.db.sql(query_delete,as_dict=1)

		return reply
	except Exception as e:
		reply['message']=str(e)
		reply['message_traceback']=str(traceback.format_exc())
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Error: Serial no not update bulk",
			message="Line 846 avdm.py <br>{} <br>{} <br>{}".format(str(e),str(reply),str(serial_no_list))
		)
	return reply

#Update DC number tick in DB
@frappe.whitelist(allow_guest=True)
def update_delivery_note_records():

	reply={}
	reply["Process_status"]="DC update process 100 in bulk"
	query = "SELECT error from `tabError Log` WHERE method='{}' LIMIT 100".format(key_dc_no)
	serial_no_list = frappe.db.sql(query)
	if len(serial_no_list)==0:
		reply["Process_status_sub"]="No dc no to update"
		return reply

	flat_list = [r[0] for r in serial_no_list]
	flat_list2 = tuple(flat_list)

	try:
		#Update DC number
		query = "UPDATE `tabDelivery Note` SET `custom_marked_in_avdm`=1 WHERE `name` IN {}".format(flat_list2)
		query = query.replace("',)","')")
		serial_no_list_update = frappe.db.sql(query,as_dict=1)

		#Delete updated DC number from log
		query_delete = "DELETE FROM `tabError Log` WHERE `method`='{}' AND `error` IN {}".format(key_dc_no,flat_list2)
		query_delete = query_delete.replace("',)","')")
		delete = frappe.db.sql(query_delete,as_dict=1)

		return reply
	except Exception as e:
		reply['message']=str(e)
		reply['message_traceback']=str(traceback.format_exc())
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Error: Delivery no not update bulk",
			message="Line 883 avdm.py <br>{} <br>{} <br>{}".format(str(e),str(reply),str(serial_no_list))
		)
	return reply



def generate_token():
	
	reply={}

	username = frappe.db.get_single_value("AVDM Setting", "username")
	password = frappe.db.get_single_value("AVDM Setting", "password")

	login_url = "{}/ErptoAVDM/Login".format(evdm_url)
	reply['request_url']=login_url
	login_headers = {
		"accept": "application/json",
	}
	login_body = {
		"username": username,
		"password": password
	}
	reply['request_body']=login_body
	response = requests.post(login_url, headers=login_headers, json=login_body)

	# Check if the response content is in bytes and decode it
	response_content = response.content
	if isinstance(response_content, bytes):
		response_content = response_content.decode('utf-8')
	
	reply['resposne_status_code']=str(response.status_code)

	response_json = json.loads(response_content)
	reply['response']=str(response_json)
	details = response_json["details"]
	api_token = details["_APIToken"]

	reply['api_token']=api_token

	#Delete token and resave in list
	query = "DELETE FROM `tabError Log` WHERE method='{}' LIMIT 1".format(key_token)
	records = frappe.db.sql(query,as_dict=1)
	errorLog(key_token,str(api_token))



	try:
		todo = frappe.get_doc({
				"doctype": "EVDM Sync Log",
				"url": str(reply['request_url']),
				"execute": True,
				"response_status": str(reply['resposne_status_code']),
				"payload": str(reply['request_body']),
				"response": str(reply['response']),
				"call_type": "EVDM Token",
			})
		todo.insert(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(title="EVDM Token Save exception:",message=str(e))










	return "Token generated and save in log"

def generate_token_pratham():
	
	reply={}

	# username = frappe.db.get_single_value("AVDM Setting", "username")
	# password = frappe.db.get_single_value("AVDM Setting", "password")

	username = "ConsumeDetailsUser"
	password = "bDFsSUhaTjlQU0FRdDhY"

	url = "{}/production/api/Authenticate/Login".format(pratham_url)

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

@frappe.whitelist(allow_guest=True)
def compare_erp_and_avdm_serial_nos():
	input_date = datetime.strptime(today(), "%Y-%m-%d").strftime("%d-%m-%y")
	dt = datetime.strptime(input_date, "%d-%m-%y")
	now = datetime.now(timezone.utc)
	dt = dt.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
	today_iso = dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
	return compare_erp_and_avdm_serial_nos_transaction_date(today_iso)

@frappe.whitelist(allow_guest=True)
def compare_erp_and_avdm_serial_nos_transaction_date(transaction_date):
	
	"""Compare ERP vs AVDM serial numbers for today and email mismatches"""

	try:
		erp_serials = get_today_delivery_items_serial_nos() or []
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error Fetching ERP Serials")
		return {"error": f"Failed to fetch ERP serials: {str(e)}"}

	reply = {}


	query = "SELECT * from `tabError Log` WHERE method='{}' LIMIT 1".format(key_token)
	token = frappe.db.sql(query,as_dict=1)

	if len(token)==0:
		generate_token()
		reply['Token_error']="Token not found"
		return reply

	url = "{}/ErptoAVDM/AVDMCheck".format(evdm_url)
	reply['request_url']=url
	payload = {"date": transaction_date}
	headers = {
		"accept": "application/json",
		"Authorization": f"Bearer {token[0]['error']}"
	}
	reply['request_body']=str(payload)
	reply['response']=''
	reply['resposne_status_code']=''
	try:
		response = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
		reply['resposne_status_code']=str(response.status_code)
		if response.status_code != 200:
			frappe.log_error("AVDM API Error compare",f"Status: {response.status_code}, Text: {response.text}")
			return {"error": f"AVDM API returned status {response.status_code}"}

		try:
			avdm_data = response.json()
			reply['response']=str(avdm_data)
		except Exception:
			frappe.log_error(message=f"Raw Response: {response.text}", title="AVDM JSON Decode Error")
			return {"error": "AVDM API did not return valid JSON", "raw_response": response.text}
	
		try:
			todo = frappe.get_doc({
					"doctype": "EVDM Sync Log",
					"url": str(reply['request_url']),
					"execute": True,
					"response_status": str(reply['resposne_status_code']),
					"payload": str(reply['request_body']),
					"response": str(reply['response']),
					"call_type": "EVDM Check",
				})
			todo.insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(title="EVDM Serial Checking exception:",message=str(e))


		avdm_serials = []
		if isinstance(avdm_data, dict):
			avdm_serials = avdm_data.get("dvcSerial", [])
		elif isinstance(avdm_data, list):
			avdm_serials = [row.get("dvcSerial") for row in avdm_data if isinstance(row, dict) and row.get("dvcSerial")]

		# Compare
		erp_exists = [s for s in erp_serials if s not in avdm_serials]
		avdm_exists = [s for s in avdm_serials if s not in erp_serials]

		#Send mail only if mismatch found
		if erp_exists or avdm_exists:
			send_mismatch_mail(erp_exists, avdm_exists,transaction_date)

		return {
			"ERP serial No Not Exists in AVDM": erp_exists,
			"AVDM serial no not exists in ERP": avdm_exists
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Compare ERP vs AVDM Error")
		return {"error": str(e)}


def get_today_delivery_items_serial_nos():
	query = """
	SELECT 
		dni.item_code,
		SUM(dni.qty) AS total_qty,
		CASE 
			WHEN dni.serial_and_batch_bundle IS NOT NULL AND dni.serial_and_batch_bundle != '' THEN 
				GROUP_CONCAT(DISTINCT sbbi.serial_no ORDER BY sbbi.serial_no SEPARATOR ',')
			WHEN dni.serial_no IS NOT NULL AND dni.serial_no != '' THEN 
				dni.serial_no
			ELSE NULL
		END AS serial_nos
	FROM 
		`tabDelivery Note Item` dni
	JOIN 
		`tabDelivery Note` dn 
		ON dn.name = dni.parent
	LEFT JOIN 
		`tabSerial and Batch Bundle` sbb
		ON sbb.name = dni.serial_and_batch_bundle
	LEFT JOIN 
		`tabSerial and Batch Entry` sbbi
		ON sbbi.parent = sbb.name
	WHERE 
		dn.posting_date = %s
		AND dn.is_return = 0
		AND dn.docstatus = 1
		AND dni.custom_abdm_enable = 1
	GROUP BY 
		dni.item_code
	"""
	data = frappe.db.sql(query, (today(),), as_dict=True)

	# Flatten ERP serial numbers
	erp_serials = []
	for row in data:
		if row.get("serial_nos"):
			erp_serials.extend(row["serial_nos"].split(","))
	return list(set(erp_serials))  # unique


def send_mismatch_mail(erp_missing, avdm_missing,transaction_date):
	"""Send email when ERP vs AVDM mismatch is found"""

	subject = "ERP vs AVDM Serial Mismatch Alert : {}".format(str(transaction_date).split('T')[0])
	recipients = ["ravi.patel@mantratec.com","abhishek.jain@mantratec.com","sajal.chandrawanshi@mantratec.com"]

	message = f"""
	<h3>ERP vs AVDM Serial Mismatch</h3>
	<p><b>ERP Not Exists in AVDM:</b></p>
	<pre>{", ".join(erp_missing) if erp_missing else "None"}</pre>
	<p><b>AVDM Not Exists in ERP:</b></p>
	<pre>{", ".join(avdm_missing) if avdm_missing else "None"}</pre>
	<br>
	<p>Regards,<br>ERPNext System</p>
	"""

	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message
		)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Mismatch Email Error")
		return False
	return True