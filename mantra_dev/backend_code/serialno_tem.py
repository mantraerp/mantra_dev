import frappe # type: ignore
from frappe import _ # type: ignore
from frappe.utils import nowdate,add_months # type: ignore
import json
import traceback
import requests # type: ignore
from mantra.backend_code.globle import errorLog,get_app_name,create_todo,send_error_message_to_developer # type: ignore
import ast
from requests.auth import HTTPBasicAuth # type: ignore

@frappe.whitelist(allow_guest=True)
def process_serial_no_for_date(first_date,last_date):
	
	if not get_app_name()=="mantra":
		return

	reply={}		
	# dc_list =frappe.get_all("Delivery Note", filters={"posting_date": transaction_date, "docstatus": 1, "is_return": 0})
	
	dc_list = frappe.get_all(
		"Delivery Note",
		filters={
			"posting_date": ["between", [first_date, last_date]],
			"docstatus": 1,
			"is_return": 0
		},
		fields=["name", "customer", "posting_date", "status"],
		order_by="posting_date asc"
	)

	reply["Total DC"]=len(dc_list)
	# return reply
	if len(dc_list)==0:
		reply['message']="no delivery note found"
		return reply

	try:
		for i in dc_list:
			frappe.enqueue(process_dc, job_name='SRExp',queue='long', timeout=3600,dc_no=i.name)

		return reply

	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		send_error_message_to_developer("Exception : Serial no expire date","serialno_tem.py - login_to_avdm <br>{}".format(str(traceback.format_exc())))

	return reply   



# M/DC/25-26/01837
# https://mantratec.milaap.ai/api/method/mantra_dev.backend_code.serialno_tem.process_dc?dc_no=M/DC/25-26/01837
@frappe.whitelist(allow_guest=True)
def process_dc(dc_no):

	if get_app_name()!="mantra":
		return "App is not mantra"

	dc_doc = frappe.get_doc("Delivery Note", dc_no)
	dc_item = dc_doc.items
	for i in dc_item:
		if i.item_code in ['P0858','P1523','P1524','P1961','P1970']:
			frappe.enqueue(process_dc_item, job_name='SRExpDC',queue='long', timeout=3600,dc_item=i.name,dc_doc=dc_doc)
		# return process_dc_item(dc_item=i.name,dc_doc=dc_doc)

	return "DC Process"


def process_dc_item(dc_item,dc_doc):
	sr_no_list=[]
	dc_doc_items = frappe.get_doc("Delivery Note Item", dc_item)


	if dc_doc_items.item_code in ['P0858','P1523','P1524','P1961','P1970']:
		item_detail = frappe.get_doc("Item", dc_doc_items.item_code)
		# if item_detail.custom_avdm_enable in [True,1]:
		# 	if dc_doc_items.custom_rd_service_time_period in [None,""," ","None"]:
		# 		frappe.sendmail(
		# 			recipients=["ravi.patel@mantratec.com","sajal.chandrawanshi@mantratec.com","abhishek.jain@mantratec.com"],
		# 			subject="Alert: serial number RD enable but month not set : {}".format(dc_doc.name),
		# 			message="Item Code:{}".format(str(dc_doc_items.item_code))
		# 		)
		# 		return

		# if item_detail.custom_rma_enable in [True,1]:
		# 	if dc_doc_items.custom_warranty_time_periodin_months in [None,""," ","None"]:
		# 		frappe.sendmail(
		# 			recipients=["ravi.patel@mantratec.com","sajal.chandrawanshi@mantratec.com","abhishek.jain@mantratec.com"],
		# 			subject="Alert: serial number RMA enable but month not set : {}".format(dc_doc.name),
		# 			message="Item Code:{}".format(str(dc_doc_items.item_code))
		# 		)
		# 		return


		if dc_doc_items.serial_no:
			sr_no = dc_doc_items.serial_no
			serial_no = sr_no.replace("\n", ",")
			serial_no_list = serial_no.split(",")
			for s_no in serial_no_list:
				sr_no_list.append(str(s_no))

		bundle_sr_no = process_dc_bundle(dc_doc.name)
		for s_no in bundle_sr_no:
			if s_no['serial_no'] not in sr_no_list:
				if s_no['item_code'] == dc_doc_items.item_code:
						sr_no_list.append(str(s_no['serial_no']))


		# for s_no in sr_no_list:
		for index, s_no in enumerate(sr_no_list):
			# if index%2==0:
			frappe.enqueue(process_dc_date_information, job_name='SRExpDate',queue='short', timeout=3600,dc_item=dc_doc_items,dc_doc=dc_doc,sr_no=s_no,item_detail=item_detail)
			# else:
			# 	frappe.enqueue(process_dc_date_information, job_name='SRExpDate',queue='default', timeout=3600,dc_item=dc_doc_items,dc_doc=dc_doc,sr_no=s_no,item_detail=item_detail)

			# return process_dc_date_information(dc_item=dc_doc_items,dc_doc=dc_doc,sr_no=s_no,item_detail=item_detail)

	return "DC item process"

def process_dc_date_information(dc_item,dc_doc,sr_no,item_detail):

	if not get_app_name()=="mantra":
		return "App is not mantra"

	reply={}
	try:
		new_warranty_date = ""
		if not dc_item.custom_warranty_time_periodin_months:
			first_obj = str(dc_item.custom_warranty_time_periodin_months).split(" ")[0]
			reply['f_o']=first_obj
			first_obj = first_obj.replace(' ', ' ')
			first_obj = first_obj.replace('\n', ' ')
			first_obj = first_obj.replace('\r', ' ')
			first_obj = str(first_obj).split(" ")[0]
			reply['first_obj']=str(first_obj)
			reply['first_obj_lower']=str(first_obj).lower()

			first_obj = 15
			# if str(first_obj).lower() not in ["no","not","","0",None]:
			new_warranty_date = add_months(dc_doc.posting_date, int(first_obj))

		new_rd_date = ""
		# if item_detail.custom_avdm_enable in [True,1]:
		# 	if dc_item.custom_rd_service_time_period:
		# 		first_obj = str(dc_item.custom_rd_service_time_period).split(" ")[0]
		# 		reply['s_o']=first_obj
		# 		first_obj = first_obj.replace(' ', ' ')
		# 		first_obj = first_obj.replace('\n', ' ')
		# 		first_obj = first_obj.replace('\r', ' ')
		# 		first_obj = str(first_obj).split(" ")[0]
		# 		reply['second_obj']=first_obj

		# 		if str(first_obj).lower() not in ["no","not","","0",None]:	
		# 			new_rd_date = add_months(dc_doc.posting_date, int(first_obj))

		reply["new_warranty_date"]=new_warranty_date
		reply["new_rd_date"]=new_rd_date

		if new_warranty_date!="":
			query_update = "UPDATE `tabSerial No` SET `warranty_expiry_date`='{}' WHERE `name`='{}'".format(new_warranty_date,sr_no)
			query_update = query_update.replace("',)","')")
			serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
			reply["o1_warranty_expiry_date"]="new_warranty_date"

		# if new_rd_date!="":
		# 	query_update = "UPDATE `tabSerial No` SET `amc_expiry_date`='{}' WHERE `name`='{}'".format(new_rd_date,sr_no)
		# 	query_update = query_update.replace("',)","')")
		# 	serial_no_list_update = frappe.db.sql(query_update,as_dict=1)
		# 	reply["o1_amc_expiry_date"]="new_rd_date"

	except Exception as e:
		reply['message']="Exception"
		reply['message_traceback']=str(traceback.format_exc())
		send_error_message_to_developer("Exception : Serial no expire date update {}".format(dc_doc.name),"serialno.py {}".format(str(reply)))

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