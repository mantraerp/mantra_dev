import frappe # type: ignore
from frappe import _ # type: ignore
from frappe.utils import nowdate,add_months # type: ignore
import json
import traceback
import requests # type: ignore
from mantra.backend_code.globle import errorLog,get_app_name,create_todo # type: ignore
import ast
from requests.auth import HTTPBasicAuth # type: ignore



@frappe.whitelist()
def serial_no_scheduled():

	if not get_app_name()=="mantra":
		return

	frappe.enqueue(process_serial_no_for_date, queue='long', timeout=3600,transaction_date=nowdate())
	return True  

@frappe.whitelist()
def process_serial_no_for_date(transaction_date):
    
	if not get_app_name()=="mantra":
		return
 
	reply={}		
	dc_list =frappe.get_all("Delivery Note", filters={"posting_date": transaction_date, "docstatus": 1, "is_return": 0})
	reply["Total DC"]=len(dc_list)
	if len(dc_list)==0:
		reply['message']="no delivery note found"
		return reply

	try:
		# query = "DELETE FROM `tabError Log` WHERE `method` IN ('{}','{}','{}','{}')".format(key_process_for_experire_date)
		# records_deleted = frappe.db.sql(query,as_dict=1)

		# generate_token()
		# generate_token_pratham()

		for i in dc_list:
			frappe.enqueue(process_dc, job_name='SRExp',queue='long', timeout=3600,dc_no=i.name)
		process_dc(dc_list)
		return reply

	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		mssage = str(traceback.format_exc())
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Exception : Serial no expire date",
			message="serialno.py - login_to_avdm <br>{}".format(mssage)
		)
	
	return reply   

# http://192.168.1.38:8001/api/method/mantra_dev.backend_code.serialno.process_dc?dc_no=M/DC/25-26/02632

@frappe.whitelist(allow_guest=True)
def process_dc(dc_no):

	if not get_app_name()=="mantra":
		return "App is not mantra"

	dc_doc = frappe.get_doc("Delivery Note", dc_no)
	dc_item = dc_doc.items
	for i in dc_item:
		# return process_dc_item(dc_item=i.name,dc_doc=dc_doc)
		frappe.enqueue(process_dc_item, job_name='SRExp',queue='long', timeout=3600,dc_item=i.name,dc_doc=dc_doc)

	return "DC Process"


def process_dc_item(dc_item,dc_doc):
	sr_no_list=[]
	dc_doc_items = frappe.get_doc("Delivery Note Item", dc_item)
	if dc_doc_items.serial_no:
		sr_no = dc_doc_items.serial_no
		serial_no = sr_no.replace("\n", ",")
		serial_no_list = serial_no.split(",")
		for s_no in serial_no_list:
			sr_no_list.append(str(s_no))

	bundle_sr_no = process_dc_bundle(dc_doc.name)
	for s_no in bundle_sr_no:
		if s_no['serial_no'] not in sr_no_list:
			if s_no['item_code'] not in dc_doc_items.item_code:
					sr_no_list.append(str(s_no['serial_no']))

	for s_no in sr_no_list:
		return process_dc_date_information(dc_item=dc_doc_items,dc_doc=dc_doc,sr_no=s_no)
		# frappe.enqueue(process_dc_date_information, job_name='SRExpDate',queue='long', timeout=3600,dc_item=dc_doc_items,dc_doc=dc_doc,sr_no=s_no)

	return "DC item process"



def process_dc_date_information(dc_item,dc_doc,sr_no):

	if not get_app_name()=="mantra":
		return "App is not mantra"

	# custom_warranty_time_periodin_months = warranty_expiry_date
	# custom_rd_service_time_period = amc_expiry_date
	reply={}
	try:
		new_warranty_date = ""
		if dc_item.custom_warranty_time_periodin_months:
			first_obj = str(dc_item.custom_warranty_time_periodin_months).split(" ")[0]
			# if str(first_obj).lower not in ["no","not","","0"]:
			if not str(first_obj).lower.startswith("no","not","","0"):
				new_warranty_date = add_months(dc_doc.posting_date, int(first_obj))

		new_rd_date = ""
		if dc_item.custom_rd_service_time_period:
			first_obj = str(dc_item.custom_rd_service_time_period).split(" ")[0]
			if not str(first_obj).lower.startswith("no","not","","0"):
				new_rd_date = add_months(dc_doc.posting_date, int(first_obj))
		reply["new_warranty_date"]=new_warranty_date
		reply["new_rd_date"]=new_rd_date

		if new_warranty_date!="" and new_rd_date!="":
			query_update = "UPDATE `tabSerial No` SET `warranty_expiry_date`='{}', `amc_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,new_rd_date,sr_no)
			query_update = query_update.replace("',)","')")
			serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
			reply["o1"]="both date update"
		else:
			if new_warranty_date!="":
				query_update = "UPDATE `tabSerial No` SET `warranty_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,sr_no)
				query_update = query_update.replace("',)","')")
				serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
				reply["o1_warranty_expiry_date"]="both date update"

			else:
				if new_rd_date!="":
					query_update = "UPDATE `tabSerial No` SET `amc_expiry_date`='{}' WHERE `name`='{}'".format(new_rd_date,sr_no)
					query_update = query_update.replace("',)","')")
					serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
					reply["o1_amc_expiry_date"]="both date update"

	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		frappe.sendmail(
			recipients=["ravi.patel@mantratec.com"],
			subject="Exception : Serial no expire date update {}".format(dc_doc.name),
			message="serialno.py {}".format(str(reply))
		)

	return reply




def process_dc_bundle(dc_no):
	
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
		""".format(dc_no)
	list_body_to_process = frappe.db.sql(query,as_dict=1)
	return list_body_to_process

