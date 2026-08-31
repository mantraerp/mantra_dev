import frappe # type: ignore
from frappe import _ # type: ignore
from frappe.utils import nowdate,add_months # type: ignore
import json
import traceback
import requests # type: ignore
from mantra.backend_code.globle import errorLog,get_app_name,create_todo,send_error_message_to_developer # type: ignore
import ast
from requests.auth import HTTPBasicAuth # type: ignore
from frappe.utils import getdate



@frappe.whitelist(allow_guest=True)
def serial_no_scheduled():

	if get_app_name() not in ["mantra","smart identity"]:
		return

	frappe.enqueue(process_serial_no_for_date, queue='long', timeout=3600,transaction_date=nowdate())
	return True  


@frappe.whitelist(allow_guest=True)
def remain_dc_to_process_sr_date(start_datetime,end_datetime):

	start_datetime = f"{start_datetime} 00:00:00.000000"
	end_datetime = f"{end_datetime} 23:59:59.000000"

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

	for dc in dc_list:
		frappe.enqueue(process_dc, job_name='DC',queue='long', timeout=1000,dc_no=dc.name)

	return len(dc_list)



@frappe.whitelist(allow_guest=True)
def process_serial_no_for_date(transaction_date):

	if get_app_name() not in ["mantra","smart identity"]:
		return

	errorLog("Serial no date update on server",str(transaction_date))

	reply={}
	# dc_list =frappe.get_all("Delivery Note", filters={"posting_date": transaction_date, "docstatus": 1, "is_return": 0})

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
		return reply

	try:
		for i in dc_list:
			frappe.enqueue(process_dc, job_name='DC',queue='long', timeout=1000,dc_no=i.name)

		return reply

	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		send_error_message_to_developer("Exception : Serial no expire date","serialno.py - login_to_avdm <br>{}".format(str(traceback.format_exc())))

	return reply



@frappe.whitelist(allow_guest=True)
def process_serial_no_for_date_without_restriction(transaction_date):

	if get_app_name() not in ["mantra","smart identity"]:
		return

	errorLog("Serial no date update on server",str(transaction_date))

	reply={}
	# dc_list =frappe.get_all("Delivery Note", filters={"posting_date": transaction_date, "docstatus": 1, "is_return": 0})

	start_datetime = f"{transaction_date} 00:00:00.000000"
	end_datetime = f"{transaction_date} 23:59:59.000000"

	dc_list = frappe.get_all(
		"Delivery Note",
		filters={
			"modified": ["between", [start_datetime, end_datetime]],
			"docstatus": 1,
			"is_return": 0,
		},
		fields=["name", "modified"]
	)

	reply["Total DC"]=len(dc_list)
	if len(dc_list)==0:
		reply['message']="no delivery note found"
		return reply

	try:
		for i in dc_list:
			frappe.enqueue(process_dc, job_name='DC',queue='long', timeout=1000,dc_no=i.name)

		return reply

	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		send_error_message_to_developer("Exception : Serial no expire date","serialno.py - login_to_avdm <br>{}".format(str(traceback.format_exc())))

	return reply 

# http://10.172.100.21:8001/api/method/mantra.backend_code.serialno.process_dc?dc_no=M/DC/25-26/06983


@frappe.whitelist(allow_guest=True)
def process_dc(dc_no):

	if get_app_name() not in ["mantra","smart identity"]:
		return "App is not mantra"

	dc_doc = frappe.get_doc("Delivery Note", dc_no)
	dc_item = dc_doc.items
	for i in dc_item:
		frappe.enqueue(process_dc_item, job_name='DCItem',queue='long', timeout=3600,dc_item=i.name,dc_doc=dc_doc)

	return "DC Process"


@frappe.whitelist(allow_guest=True)
def process_dc_dl(doc, method=None):

	if get_app_name() not in ["mantra","smart identity"]:
		return "App is not mantra"

	dc_doc = frappe.get_doc("Delivery Note", doc.name)
	dc_item = dc_doc.items
	for i in dc_item:
		frappe.enqueue(process_dc_item, job_name='DCItem',queue='long', timeout=3600,dc_item=i.name,dc_doc=dc_doc)

	return "DC Process"



@frappe.whitelist(allow_guest=True)
def process_dc_api(dc_no):

	if get_app_name() not in ["mantra","smart identity"]:
		return "App is not mantra"

	dc_doc = frappe.get_doc("Delivery Note", dc_no)
	dc_item = dc_doc.items
	for i in dc_item:
		frappe.enqueue(process_dc_item, job_name='DCItem',queue='default', timeout=3600,dc_item=i.name,dc_doc=dc_doc)

	return "DC Process"



def item_detail_update(dc_item,dc_doc):

	dc_doc_items = frappe.get_doc("Delivery Note Item", dc_item)
	item_detail = frappe.get_doc("Item", dc_doc_items.item_code)
	if item_detail.custom_avdm_enable in [True,1]:
		#Main serial no validation
		if dc_doc_items.custom_rd_service_time_period in [None,""," ","None","Not Applicable","No Warranty"]:
			# if dc_doc_items.custom_warranty_time_periodin_months not in [None,""," ","None","Not Applicable","No Warranty"]:
			# 	#If AVDM enable but month not set then require to set same month as RMA
			# 	query = "UPDATE `tabDelivery Note Item` SET `custom_rd_service_time_period`='{}' WHERE `name` = '{}'".format(dc_doc_items.custom_warranty_time_periodin_months,dc_doc_items.name)
			# 	records = frappe.db.sql(query,as_dict=1)
			# else:
			if item_detail.custom_rd_service_minimum_time_period not in [None,""," ","None","Not Applicable","No Warranty"]:
				# If RAM month not found then check in item minimum month is set. If yes then set it
				query = "UPDATE `tabDelivery Note Item` SET `custom_rd_service_time_period`='{}' WHERE `name` = '{}'".format(item_detail.custom_rd_service_minimum_time_period,dc_doc_items.name)
				records = frappe.db.sql(query,as_dict=1)
	else:
		#Check for sub serial no
		if item_detail.custom_submodel_avdm_enable in [True,1]:
			if dc_doc_items.custom_rd_service_time_period in [None,""," ","None","Not Applicable","No Warranty"]:
				# if dc_doc_items.custom_warranty_time_periodin_months not in [None,""," ","None","Not Applicable","No Warranty"]:
				# 	#If AVDM enable but month not set then require to set same month as RMA
				# 	query = "UPDATE `tabDelivery Note Item` SET `custom_rd_service_time_period`='{}' WHERE `name` = '{}'".format(dc_doc_items.custom_warranty_time_periodin_months,dc_doc_items.name)
				# 	records = frappe.db.sql(query,as_dict=1)
				# else:
				if item_detail.custom_rd_service_minimum_time_period not in [None,""," ","None","Not Applicable","No Warranty"]:
					# If RAM month not found then check in item minimum month is set. If yes then set it
					query = "UPDATE `tabDelivery Note Item` SET `custom_rd_service_time_period`='{}' WHERE `name` = '{}'".format(item_detail.custom_rd_service_minimum_time_period,dc_doc_items.name)
					records = frappe.db.sql(query,as_dict=1)

# http://10.172.100.21:8001/api/method/mantra.backend_code.serialno.process_dc_item?dc_no=M/DC/25-26/02734
def process_dc_item(dc_item,dc_doc):

	item_detail_update(dc_item,dc_doc)

	sr_no_list=[]
	dc_doc_items = frappe.get_doc("Delivery Note Item", dc_item)

	item_detail = frappe.get_doc("Item", dc_doc_items.item_code)
	if item_detail.custom_avdm_enable in [True,1]:
		if dc_doc_items.custom_rd_service_time_period in [None,""," ","None"]:
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com","abhishek.jain@mantratec.com"],
				subject="Alert: serial number RD enable but month not set : {}".format(dc_doc.name),
				message="Item Code:{}".format(str(dc_doc_items.item_code))
			)
			return

	if item_detail.custom_rma_enable in [True,1]:
		if dc_doc_items.custom_warranty_time_periodin_months in [None,""," ","None"]:
			frappe.sendmail(
				recipients=["ravi.patel@mantratec.com","sajal.chandrawanshi@mantratec.com","abhishek.jain@mantratec.com"],
				subject="Alert: serial number RMA enable but month not set : {}".format(dc_doc.name),
				message="Item Code:{}".format(str(dc_doc_items.item_code))
			)
			# return

	if dc_doc_items.serial_no:
		sr_no = dc_doc_items.serial_no
		serial_no = sr_no.replace("\n", ",")
		serial_no_list = serial_no.split(",")
		for s_no in serial_no_list:
			sr_no_list.append(str(s_no))

	if dc_doc_items.serial_and_batch_bundle:
		bundle_sr_no = process_dc_bundle(dc_doc.name,dc_doc_items.serial_and_batch_bundle)
		for s_no in bundle_sr_no:
			if s_no['serial_no'] not in sr_no_list:
				if s_no['item_code'] == dc_doc_items.item_code:
						sr_no_list.append(str(s_no['serial_no']))


	#Remove duplicate
	unique_list = []
	seen = set()

	for item in sr_no_list:
		if item not in seen:
			seen.add(item)
			unique_list.append(item)


	for s_no in unique_list:
		frappe.enqueue(process_dc_date_information, job_name='SRExpDate',queue='default', timeout=3600,dc_item=dc_doc_items,dc_doc=dc_doc,sr_no=s_no,item_detail=item_detail)

	return "DC item process"

def process_dc_date_information(dc_item,dc_doc,sr_no,item_detail):

	if get_app_name() not in ["mantra","smart identity"]:
		return "App is not mantra"

	sr_no = sr_no.replace("',)","')")
	# custom_warranty_time_periodin_months = warranty_expiry_date
	# custom_rd_service_time_period = amc_expiry_date
	reply={}
	try:
		new_warranty_date = ""
		# if item_detail.custom_rma_enable in [True,1]:
		if dc_item.custom_warranty_time_periodin_months:
			first_obj = str(dc_item.custom_warranty_time_periodin_months).split(" ")[0]
			reply['f_o']=first_obj
			first_obj = first_obj.replace(' ', ' ')
			first_obj = first_obj.replace('\n', ' ')
			first_obj = first_obj.replace('\r', ' ')
			first_obj = str(first_obj).split(" ")[0]
			reply['first_obj']=str(first_obj)
			reply['first_obj_lower']=str(first_obj).lower()

			if str(first_obj).lower() not in ["no","not","","0",None]:
				month_to_add = int(first_obj)
				if month_to_add == 12:
					month_to_add = 15
				new_warranty_date = add_months(dc_doc.posting_date, month_to_add)

		new_rd_date = ""
		if item_detail.custom_avdm_enable in [True,1]:
			if dc_item.custom_rd_service_time_period:
				second_obj = str(dc_item.custom_rd_service_time_period).split(" ")[0]
				reply['s_o']=second_obj
				second_obj = second_obj.replace(' ', ' ')
				second_obj = second_obj.replace('\n', ' ')
				second_obj = second_obj.replace('\r', ' ')
				second_obj = str(second_obj).split(" ")[0]
				reply['second_obj']=second_obj

				if str(second_obj).lower() not in ["no","not","","0",None]:
					if int(second_obj)==12:
						second_obj = 15
					else:
						second_obj = int(second_obj)	
					new_rd_date = add_months(dc_doc.posting_date, second_obj)

		reply["new_warranty_date"]=new_warranty_date
		reply["new_rd_date"]=new_rd_date


		query_update = "SELECT warranty_expiry_date,amc_expiry_date FROM `tabSerial No` WHERE `name`='{}'".format(sr_no)
		sr_no_details = frappe.db.sql(query_update,as_dict=1)

		if len(sr_no_details)!=0:
			if new_warranty_date!="":
				erp_rma = sr_no_details[0]['warranty_expiry_date']
				if erp_rma not in ['None',None,' ','']:
					if str(erp_rma) != str(new_warranty_date):
						erp_date_object = getdate(erp_rma)
						avdm_date_object = getdate(new_warranty_date)
						#If ERP date is bigger then only update date.
						if avdm_date_object > erp_date_object:
							query_update = "UPDATE `tabSerial No` SET `warranty_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,sr_no)
							query_update = query_update.replace("',)","')")
							serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
							reply["o1_warranty_expiry_date"]=query_update
				else:
					query_update = "UPDATE `tabSerial No` SET `warranty_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,sr_no)
					query_update = query_update.replace("',)","')")
					serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
					reply["o1_warranty_expiry_date"]=query_update

			if new_rd_date!="":
				erp_rd = sr_no_details[0]['amc_expiry_date']
				if erp_rd not in ['None',None,' ','']:
					if str(erp_rd) != str(new_rd_date):
						erp_date_rd_object = getdate(erp_rd)
						avdm_date_rd_object = getdate(new_rd_date)
						#If ERP date is bigger then only update date.
						if avdm_date_rd_object > erp_date_rd_object:
							query_update = "UPDATE `tabSerial No` SET `amc_expiry_date`='{}' WHERE `name`='{}'".format(new_rd_date,sr_no)
							query_update = query_update.replace("',)","')")
							serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
							reply["o1_amc_expiry_date"]=query_update
				else:
					query_update = "UPDATE `tabSerial No` SET `amc_expiry_date`='{}' WHERE `name`='{}'".format(new_rd_date,sr_no)
					query_update = query_update.replace("',)","')")
					serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
					reply["o1_amc_expiry_date"]=query_update
		else:
			send_error_message_to_developer("SR Not Found: {}".format(sr_no),"DC details {}<br>DC item detail {}".format(str(dc_doc),str(dc_item)))

	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		send_error_message_to_developer("Exception : Serial no expire date update {}".format(dc_doc.name),"serialno.py {}".format(str(reply)))

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




# http://10.172.100.21:8001/api/method/mantra.backend_code.serialno.get_serial_no_history?sr_no=9408938

@frappe.whitelist(allow_guest=True)
def get_serial_no_history(sr_no):

	query = """
	SELECT
		sle.posting_date,
		sle.voucher_type,
		sle.voucher_no,
		sle.warehouse,
		sle.actual_qty,
		sle.qty_after_transaction
	FROM
		`tabStock Ledger Entry` sle
	WHERE
		sle.serial_no = '{}'
	ORDER BY
		sle.posting_date DESC;
		""".format(sr_no)
	list_body_to_process = frappe.db.sql(query,as_dict=1)


	if len(list_body_to_process)==0:
		query = """
			SELECT
				sle.posting_date,
				sle.voucher_type,
				sle.voucher_no,
				sle.warehouse,
				sle.actual_qty,
				sle.qty_after_transaction
			FROM
				`tabSerial and Batch Entry` sbe
			WHERE
				sle.serial_no = '{}'
			ORDER BY
				sle.posting_date DESC;
				""".format(sr_no)
		list_body_to_process = frappe.db.sql(query,as_dict=1)

	return list_body_to_process