from frappe.model.document import Document # type: ignore
import frappe # type: ignore
import requests # type: ignore
import traceback

import json
# from datetime import datetime,timedelta
from frappe.utils import getdate # type: ignore


producation_mode = False



class MinopSetting(Document):
	pass


################################## Employee status sync #####################
@frappe.whitelist()
def cron_employee_sync():
	frappe.enqueue(sync_employee_status,PunchID="0", queue='long', timeout=10000)
	return True

@frappe.whitelist(allow_guest=True)
def sync_employee_status(PunchID):
    
	reply = {}
	reply["status_code"]=200
	reply["message"]=""
    
	try:
		endpoints = frappe.db.get_single_value("ERP Settings","end_point")
		key = frappe.db.get_single_value("ERP Settings","key")

		url = f"{endpoints}/Transaction/GetERPEmployeeDataApi"
		headers = {
			"Apisubkey" : key
		}
		payload = {
			"PunchID" : PunchID 
		}
		response = requests.get(url,headers=headers,json=payload)
		data = response.json()
		if data:
			for d in data:
				frappe.enqueue(sync_employee_status_background,record=d, queue='long', timeout=10000)
		else:
			reply["message"]="Punch id not found"
   
		return reply
  
	except Exception as e:
		error_message = "{}<br>sync_employee_status<br><br>{}".format(str(e),str(traceback.format_exc()))
		send_error_mail("Error syncing employee status",error_message)
		reply["status_code"]=500
		reply["message"]=str(e)
  
	return reply

#Employee Status Checking Active or Inactive
#Check with permission of hr role
@frappe.whitelist()
def sync_employee_status_background(record):

	reply = {}
	reply["status_code"]=200
	reply["message"]="No change in employee status."
 
	try:
		emp_code = record.get("Empcode")
		emp_status = record.get("EmpStatus")
		erp_employee = frappe.get_value("Employee",{"name":emp_code},"status")
		if not erp_employee:
			send_mail_hr_team("Employee not found in ERP {}".format(emp_code),"Employee code not found in ERP but in Minop employee is there. Please do needful.")
			send_error_mail("Employee not found in ERP {}".format(emp_code),"Employee code not found in ERP but in Minop employee is there. Please do needful.")
			reply["status_code"]=500
			reply["message"]="Employee not found in ERP {}".format(emp_code)
			return reply

		if emp_status == "Active" and erp_employee != "Active":
			frappe.db.set_value("Employee", {"name": emp_code}, "status", "Active")
			reply["message"]="Employee status set to active {}".format(emp_code)
			send_mail_hr_team("Employee status set to active {}".format(emp_code),"Employee is active on Minop but not in ERP so it set to active in erp.")

		elif emp_status == "InActive" and erp_employee != "Inactive":
			frappe.db.set_value("Employee", {"name": emp_code}, "status", "Inactive")
			reply["message"]="Employee status set to Inactive {}".format(emp_code)
			send_mail_hr_team("Employee status set to Inactive {}".format(emp_code),"Employee is Inactive on Minop but not in ERP so it set to Inactive in erp.")

		# frappe.db.commit()
		return reply
	except Exception as e:
		error_message = "{}<br>sync_employee_status_background<br><br>{}".format(str(e),str(traceback.format_exc()))
		send_error_mail("Error syncing employee status",error_message)
		reply["status_code"]=500
		reply["message"]=str(e)

	return reply


def send_error_mail(subject,message):

	frappe.sendmail(
		recipients=["ravi.patel@mantratec.com"],
		subject=subject,
		message=message,
	)
	return True

def send_mail_hr_team(subject,message):

	recipients=["ravi.patel@mantratec.com"]
	if producation_mode:
		recipients=["hrops@mantratec.com","mukund.kotadia@mantratec.com","anil.vadhel@mantratec.com"]
	
	frappe.sendmail(
		recipients=recipients,
		subject=subject,
		message=message,
	)
	return True
###################################################################################




@frappe.whitelist(allow_guest=True)
def get_attendance_process(fromdatetime,todatetime,Emp_Code=None,department=None):
    
	'''
		Sync the attendace an employee wise and if the employee 
		is defined then that employee attendance url is created 
		if employee is not defined then all active employee attendace is create
	'''
	reply = {}
	reply["status_code"]=200
	reply["message"]=""
	
	if not Emp_Code:
		Emp_Code = "0"

	if not fromdatetime or not todatetime:
		reply["message"]="From Date And To Date Is Not Found"
		return reply
	
	if fromdatetime > todatetime:
		reply["message"]="From Date is not Bigger Than To date"
		return reply     
	
	if (getdate(todatetime) - getdate(fromdatetime)).days > 31:
		reply["message"]="You can not select the more than 31 Days"
		return reply		

	if Emp_Code and Emp_Code != "0" and department:
		dept = frappe.get_value("Employee",{"name":Emp_Code}, "department")
		if dept != department:
			reply["message"]="Employee {} not belong to the department {}".format(Emp_Code,department)
			return reply

	
	endpoints = frappe.db.get_single_value("ERP Settings","end_point")
	url = f"{endpoints}Transaction/GetERPProcessdataApi"
	if Emp_Code!="0":
		emp_status = frappe.get_value("Employee",{"name":Emp_Code},"status")
		if emp_status == "InActive":
			reply["message"]="Employee {} is InActive".format(Emp_Code)
			return reply

		att_url = f"{url}"
		payload = {
			"Emp_Code": Emp_Code,
			"fromdatetime": fromdatetime,
			"todatetime": todatetime
		}
		add_url(att_url,payload)
		#start 1 min cron
		frappe.enqueue(start_url_fetching_cron, queue='long', timeout=10000)
		reply["message"]="Proccess for data for {}".format(Emp_Code)
		return reply
	
	elif Emp_Code=="0":
		query = "SELECT name FROM `tabEmployee` WHERE `status`='Active'"
		if department:
			query += f" AND department = '{department}'"

		emp_list =frappe.db.sql(query,as_dict=True)
		for emp in emp_list:
			att_url = f"{url}"
			payload = {
				"Emp_Code": emp['name'],
				"fromdatetime": fromdatetime,
				"todatetime": todatetime
			}
			frappe.enqueue(add_url, url=att_url, payload=payload, queue='long', timeout=10000)
		#start 1 min cron
		frappe.enqueue(start_url_fetching_cron, queue='long', timeout=10000,value=0)
  
		reply["message"]="Start proccess for data with all employee in background once its done we will send the emial"
		return reply
	
	reply["status_code"]=200
	reply["message"]="Not match with any employee"
	return reply

def start_url_fetching_cron(value):
	query = "UPDATE `tabScheduled Job Type` SET `stopped`={} WHERE `method` = '{}'".format(value,'mantra_dev.mantra_dev.doctype.minop_setting.minop_setting.url_cron_process')
	records = frappe.db.sql(query,as_dict=1)
    

def add_url(url,payload):

	''' Url creation function '''

	if frappe.db.exists("Attendance Sync Log",{'payload':frappe.as_json(payload),'execute':False}):
		return f"Record is Alrady Exists"

	at_url = frappe.new_doc("Attendance Sync Log")
	at_url.url = url
	at_url.payload = frappe.as_json(payload)
	at_url.save(ignore_permissions=True)



@frappe.whitelist(allow_guest=True)
def url_cron_process():
	''' Process the background and create the attendance log 
		create for employee wise and all response store in 
		the attendance error log 
	'''

	limit_records = 5

	query = "SELECT name,url,payload FROM `tabAttendance Sync Log` WHERE `execute`= 0 ORDER BY `modified` DESC LIMIT {}".format(limit_records)
	url_list =frappe.db.sql(query,as_dict=True)
	for url in url_list:
		frappe.enqueue(url_featching_process, record=url, queue='long', timeout=10000)

	if len(url_list)==0:
		cron_sync_attendance()

	return "Proccess {} records".format(limit_records)

@frappe.whitelist(allow_guest=True)
def url_featching_process(record):
	'''
		Response fatching from the api
	'''
	reply = {}
	reply["status_code"]=200
	reply["message"]=""

	key = frappe.db.get_single_value("ERP Settings","key")
	headers = {
		"Apisubkey" : key
	}

	try:
		payload = json.loads(record["payload"])
		response = requests.post(record['url'],headers=headers,json=payload)
		status_code = response.status_code
		data = response.json()
		#store reponse in URL record
		response_status = "Error"
  
		if status_code == 200:
			response_status = "Success"
			if data:
				for rec in data:
        
					if rec['Emp_Code'] in ['MN001313','C023']:
						frappe.log_error("Selected employee attendance done","")
        
					if frappe.db.exists("Attendance Error Log", {'emp_id':rec.get("Emp_Code"),'at_date':rec.get('Date')}):
						continue
					att_data = frappe.get_doc({
						"doctype":"Attendance Error Log",
						"emp_id": rec.get("Emp_Code"),
						"at_date": rec.get("Date"),
						"m_status" : rec.get("Status"),
						"half_day" : rec.get("half_day"),
						"leave_type" : rec.get("leave_type"),
						"leave" : rec.get("leave")
					})
					current_user = frappe.session.user
					frappe.set_user("Administrator")
					att_data.save(ignore_permissions=True)
					frappe.set_user(current_user)

		query = """UPDATE `tabAttendance Sync Log` SET `execute` = 1, `response_status` = %s, `response` = %s WHERE `name` = %s"""
		frappe.db.sql(query, (response_status, json.dumps(data), record["name"]))
		reply["message"]="Url process done"
		return reply
	
	except Exception as e:
		error_message = "{}<br>url_featching_process<br><br>{}".format(str(e),str(traceback.format_exc()))
		send_error_mail("Error syncing employee status",error_message)
		reply["status_code"]=500
		reply["message"]=str(error_message)
  
	return reply

@frappe.whitelist(allow_guest=True)
def cron_sync_attendance():
	'''
		Create the attendance in the bulk and in the background 	
	'''

	limit_records = 1
	emp_id_filter = "MN001250"
	query = f"SELECT name, emp_id FROM `tabAttendance Error Log` WHERE `sync`=0 AND `emp_id`='{emp_id_filter}' LIMIT {limit_records}"
	# query = "SELECT name,emp_id FROM `tabAttendance Error Log` WHERE `sync`=0 LIMIT {}".format(limit_records)
	employee_id_list = frappe.db.sql(query,as_dict=True)
	
 
	attendances=[]
	if len(employee_id_list)!=0:
		for employee in employee_id_list:
			query = "SELECT name FROM `tabAttendance Error Log` WHERE `sync`=0 AND `emp_id`='{}'".format(employee['emp_id'])
			attendances_temp = frappe.db.sql(query,as_dict=True)
			for att in attendances_temp:
				attendances.append(att)
 

 
	for at in attendances:
		frappe.enqueue(create_attendance, rec=at['name'], queue='long', timeout=10000)

	#Checka nd stop 1 min cron
	if len(attendances)==0:
		query = "SELECT name,url,payload FROM `tabAttendance Sync Log` WHERE `execute`=0 ORDER BY `modified` DESC LIMIT 5"
		url_list =frappe.db.sql(query,as_dict=True)
		if len(url_list)==0:
			#stop 1 min cron
			frappe.enqueue(start_url_fetching_cron, queue='long', timeout=10000,value=1)
			frappe.db.commit()
			send_mail_hr_team("Last sync process is done","")
			send_error_mail("Last sync process is done","")

	return True

def create_attendance(rec):
	'''
		Create the attendance function	
	'''
	
	reply = {}
	reply["status_code"]=200
	reply["message"]=""

	try:
		att_doc = frappe.get_doc("Attendance Error Log",rec)
		if att_doc:
			exist = frappe.db.exists("Attendance",{"employee":att_doc.emp_id,"attendance_date": att_doc.at_date})
			if exist:
				reply["message"] = f"Attendance already exists for {att_doc.emp_id} on {att_doc.at_date}. Skipping."
				return reply

			attendance = frappe.new_doc("Attendance")
			attendance.employee = att_doc.emp_id
			attendance.attendance_date = att_doc.at_date
			attendance.custom_minop_status = att_doc.m_status
   
			if att_doc.m_status in ["P","PW","PH","W","WH","H","HW"]:
				attendance.status = "Present"
			elif att_doc.m_status == "A" and att_doc.leave_type == "Paid":
				if att_doc.leave in ['HTL','HCL','HSL','HWL','HML','HML','HBL','HBR','HLL','HCO','HEL','HOD']:
					attendance.status = "Half Day"
					attendance.leave_type = att_doc.leave[1:]
			elif att_doc.m_status == "A" and att_doc.leave_type == "Unpaid":
				attendance.status = "On Leave"
				attendance.leave_type = "Leave Without Pay"
			elif att_doc.m_status in ["A","XX"]:
				attendance.status = "Absent"
			elif att_doc.m_status in ["TL", "CL", "SL", "WL", "ML", "BL", "BR", "LL", "CO", "EL", "OD",'LC']:
				if att_doc.leave_type == "Paid":
					attendance.status = "On Leave"
					leavs = att_doc.leave.split(",")
					if len(leavs) > 1:
						attendance.leave_type = "LC"
					else:
						attendance.leave_type = att_doc.leave
				elif att_doc.leave_type == "Unpaid":
					attendance.status = "On Leave"
					attendance.leave_type = "Leave Without Pay"
				elif not att_doc.leave_type and att_doc.leave:
					attendance.status = "On Leave"
					attendance.leave_type = "Leave Without Pay"
			elif att_doc.m_status in ["HD","LH","E","LC"]:
				if att_doc.leave_type == "Paid":
					attendance.status = "Half Day"
					leavs = att_doc.leave.split(",")
					if len(leavs) > 1:
						attendance.leave_type = "LC"
					elif att_doc.leave == "OD":
						attendance.leave_type = att_doc.leave
					else:
						attendance.leave_type = att_doc.leave[1:]
				elif att_doc.leave_type == "Unpaid":
					attendance.status = "Half Day"
					attendance.leave_type = "Leave Without Pay"
				elif not att_doc.leave_type or not att_doc.leave:
					attendance.status = "Half Day"
					attendance.leave_type = "Leave Without Pay"
     
			attendance.save(ignore_permissions=True)
			attendance.submit()
			
			query = """UPDATE `tabAttendance Error Log` SET `sync` = 1 WHERE `name` = %s"""
			frappe.db.sql(query,rec,as_dict=True)
			# frappe.db.set_value("Attendance Error Log", rec, "sync", 1)
		else:
			send_error_mail("Error Create the Employee Attendance. Recrod not found.create_attendance",rec)
	
	except Exception as e:
		error_message = "{}<br>create_attendance<br><br>{}".format(str(e),str(traceback.format_exc()))
		send_error_mail("Error Create the Employee Attendance",error_message)
		reply["status_code"]=500
		reply["message"]=str(e)
	return reply