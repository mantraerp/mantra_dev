import frappe
from frappe import _
from frappe.utils import nowdate
import json
import traceback
import requests
from mantra_dev.backend_code.globle import errorLog,errorLogExites


@frappe.whitelist()
def login_to_avdm_scheduled():
    frappe.enqueue(login_to_avdm, queue='long', timeout=3600,transaction_date=nowdate())
    return True  

@frappe.whitelist(allow_guest=True)
def process_to_avdm_for_date(transaction_date):
    return login_to_avdm(transaction_date)

@frappe.whitelist()
def login_to_avdm(transaction_date):
    
    errorLog('AVDM',"Cron call",False)
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

            # dc_list = frappe.get_list("Delivery Note", filters={"posting_date": nowdate(), "docstatus": 1})
            # dc_list = frappe.get_all("Delivery Note", filters={"posting_date": transaction_date, "docstatus": 1})

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
            
            response1 = requests.post(creating_url, headers=headers, json=body)
            if response1.status_code==200:
                dc_response_content = response1.content
                if isinstance(dc_response_content, bytes):
                    dc_response_content = dc_response_content.decode('utf-8')

                dc_response_json = json.loads(dc_response_content)
                
                
                if dc_response_json:
                    response_serial_no = []
                    count = 0
                    for i in dc_response_json:
                        print("serial_no: ", i['devicesr'])
                        response_serial_no.append(i['devicesr'])
    

                    result = []
                    dc_dict = {}

                    # Iterate through each item in the data list
                    for item in body:
                        dc_no = item['dcNo']
                        serial_no = item['serialNo']
                        
                        # Check if the dcNo already exists in the dictionary
                        if dc_no in dc_dict:
                            # Append the serialNo to the existing key
                            dc_dict[dc_no].append(serial_no)
                        else:
                            # Create a new dictionary with dcNo as key and serialNo as value in a list
                            dc_dict[dc_no] = [serial_no]

                    # Convert the dictionary into a list of dictionaries
                    for key, value in dc_dict.items():
                        result.append({key: value})
                                        
                    for i in result:
                        for key, values in i.items():
                            # print(key, values)
                            for j in values:
                                if j in response_serial_no:
                                    # frappe.db.set_value('Serial No', j, 'custom_marked_in_avdm', 1)
                                    frappe.enqueue(update_serial_no_field,queue='long',job_name="Update serial no {}".format(serial_no),timeout=100000,serial_no=j)
                                else:
                                    count = count + 1
                        if count == 0:
                            # frappe.db.set_value('Delivery Note', key, 'custom_marked_in_avdm', 1)
                            frappe.enqueue(update_delivery_field,queue='long',job_name="Update delivery note {}".format(key),timeout=100000,dc_no=key)
                            # frappe.db.commit()
                        else:
                            pass
                    # frappe.db.commit()

                errorLog('AVDM-End-S',"Cron call",False)
            else :
                dc_response_json=response1.status_code
                frappe.sendmail(
                    recipients=["ravi.patel@mantratec.com"],
                    subject="AVDM not process due to issue",
                    message="Line 141 api.py"
                )
            # dc_details = dc_response_json["details"]
            # print(f"Details :{ dc_details }")
            # details_json = json.loads(details)
            # dc_api_token = dc_details["_APIToken"]
            # print(f"API Token: {dc_api_token}")        
            # return body
            reply['message']="Process"
            return dc_response_json 
            # return "jfgh", response_content
        except Exception as e:
            reply['message']="Exception"
            reply['message_traceback']=str(traceback.format_exc())
            mssage = str(traceback.format_exc())
            frappe.sendmail(
                recipients=["ravi.patel@mantratec.com"],
                subject="AVDM not process due to issue",
                message="Line 156 api.py <br>{}".format(mssage)
            )
    else:
        reply['message']="AVDM setting is not enable"
        
    return reply        
 
def update_serial_no_field(serial_no):
    frappe.db.set_value('Serial No', serial_no, 'custom_marked_in_avdm', 1)
    return True
 
def update_delivery_field(dc_no):
    frappe.db.set_value('Delivery Note', dc_no, 'custom_marked_in_avdm', 1)
    return True