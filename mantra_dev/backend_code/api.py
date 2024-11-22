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
def add_bank_account(account_table, doc, name1):
    doc = json.loads(doc)
    bank_account = frappe.new_doc('Bank Account')
    bank_account.account_name = doc.get('account_name')
    bank_account.bank = doc.get('bank')
    bank_account.party = name1
    bank_account.bank_account_no = doc.get('bank_account_no')
    bank_account.custom_branch_location = doc.get('branch_location')
    bank_account.branch_code = doc.get('branch_code')
    bank_account.custom_ifsc = doc.get('ifsc')
    bank_account.party_type = "Supplier"
    
    # Link to the Supplier
    bank_account.parent = name1  # Supplier name
    bank_account.parenttype = "Supplier"
    bank_account.parentfield = "custom_bank_account_table"
    bank_account.insert()
    frappe.db.commit()
    # fetch_existing_documents(doc, name)
    if account_table:
        doc = account_table
        name = name1
        fetch_existing_documents(doc, name)
    return "heyyy"



@frappe.whitelist()
def fetch_existing_documents(doc,name):
    get_all_accounts = frappe.get_all('Bank Account',filters={'party': name},fields=['*'],)
    document = frappe.get_doc("Supplier",name)
    document.set("custom_bank_account_table", [])
    if get_all_accounts:
        document.save()
        for j in get_all_accounts:
            row = {
            "workflow_state" : j.workflow_state,
            "account_name" : j.account_name,
            "bank_account_no" : j.bank_account_no,
            "bank" : j.bank,
            "branch_location" : j.custom_branch_location,
            "branch_code" : j.branch_code,
            "ifsc" : j.custom_ifsc,
            }
            document.append("custom_bank_account_table", row)
            document.save()
    document.save()
    frappe.db.set_value('Supplier', name, "custom_update_data", 0)

@frappe.whitelist()
def fetch_workflow_state(doc,name): 
    get_all_accounts = frappe.get_all('Bank Account',filters={'party': name},fields=['*'],)
    doc = json.loads(doc)
    nnnn=''
    # doc.set("custom_bank_account_table", [])
    for i in doc:
        for j in get_all_accounts:
            if i.get('bank_account_no') in j.bank_account_no:
                state = j.workflow_state
                acc_name = j.account_name
                acc_num = j.bank_account_no
                acc_bank = j.bank
                acc_branch_location = j.custom_branch_location
                acc_branch_code = j.branch_code
                acc_ifsc = j.custom_ifsc
                n = i.get('name')
                frappe.db.set_value('Bank Account Table', n, "workflow_state", state)
                frappe.db.set_value('Bank Account Table', n, "account_name", acc_name)
                frappe.db.set_value('Bank Account Table', n, "bank_account_no", acc_num)
                frappe.db.set_value('Bank Account Table', n, "bank", acc_bank)
                frappe.db.set_value('Bank Account Table', n, "branch_location", acc_branch_location)
                frappe.db.set_value('Bank Account Table', n, "branch_code", acc_branch_code)
                frappe.db.set_value('Bank Account Table', n, "ifsc", acc_ifsc)
                nnnn = j

    frappe.db.set_value('Supplier', name, "custom_update_data", 0)
    frappe.db.commit()
    return nnnn



@frappe.whitelist()
def create_bank_account(doc,name):
    doc = json.loads(doc)
    for i in doc:
        bank_account = frappe.new_doc('Bank Account')
        bank_account.account_name = i.get('account_name')
        bank_account.bank = i.get('bank')
        bank_account.party = name
        bank_account.bank_account_no = i.get('bank_account_no')
        bank_account.custom_branch_location = i.get('branch_location')
        bank_account.branch_code = i.get('branch_code')
        bank_account.custom_ifsc = i.get('ifsc')
        bank_account.party_type = "Supplier"
        
        # Link to the Supplier
        bank_account.parent = name  # Supplier name
        bank_account.parenttype = "Supplier"
        bank_account.parentfield = "custom_bank_account_table"
        bank_account.insert()
    frappe.db.commit()
    return "hello"







@frappe.whitelist()
def get_party_name(party_type,party):
    if party_type == "Supplier":
        sup_name = frappe.db.sql("select supplier_name from `tabSupplier` where name = %s ", (party), as_dict = True)
        if sup_name :
            supplier_name = sup_name[0]["supplier_name"]
            return supplier_name
    elif party_type == "Customer":
        cust_name = frappe.db.sql("select customer_name from `tabCustomer` where name = %s ", (party), as_dict = True)
        if cust_name :
            customer_name = cust_name[0]["customer_name"]
            return customer_name
    elif party_type == "Employee":
        emp_name = frappe.db.sql("select employee_name from `tabEmployee` where name = %s ", (party), as_dict = True)
        if emp_name :
            employee_name = emp_name[0]["employee_name"]
            return employee_name
    else:
        frappe.msgprint("Not Found")


@frappe.whitelist()
def purchase_receipt_check_box(invoice_name, invoice_docstatus):

    purchase_receipt_list1 = []
    document = frappe.get_doc('Purchase Invoice', invoice_name)

    items = document.items
    for i in items:
        purchase_receipt_list1.append(i.purchase_receipt)
    purchase_receipt_list1 = set(purchase_receipt_list1)
    purchase_receipt_list1 = list(purchase_receipt_list1)
    
    for i in purchase_receipt_list1:
        docstatus = str(frappe.db.get_value('Purchase Receipt', i,'docstatus'))
        status = frappe.db.get_value('Purchase Receipt', i,'status')
        if invoice_docstatus == '0':
            frappe.db.set_value('Purchase Receipt',i, 'custom_processed', 1)
            frappe.db.commit()
            break
        if docstatus == '1':
            # frappe.msgprint(i)
            frappe.db.set_value('Purchase Receipt',i, 'custom_processed', 0)
            frappe.db.commit()

        
@frappe.whitelist()
def warehouse_manager_data_fetch_stock_entry(mr_no):
    tw = frappe.db.sql("SELECT set_warehouse FROM `tabMaterial Request` WHERE name = %s", (mr_no,))

    set_tw = tw[0][0]  # Extracting the value from the first tuple in the list
    # frappe.msgprint(set_tw)

    warehouse_manager = []

    wm = frappe.db.sql("select warehouse_manager from `tabWarehouse Manager` where parent = %s ", (set_tw,))

    # for record in wm:
    #     warehouse_manager.append(record["warehouse_manager"])

    # Assign the string to frappe.response["message"]
    return wm    

@frappe.whitelist()
def warehouse_manager_data_fetch_material_request(warehouse):
    warehouse_manager = []

    wm = frappe.db.sql("select warehouse_manager from `tabWarehouse Manager` where parent = %s ",(warehouse))
                
    # for record in wm:
    #         warehouse_manager.append(record)

    return wm

@frappe.whitelist()
def get_opration_approver(department):
    # frappe.msgprint(str(department))
    doc=frappe.get_doc("Department",department)
    dep_approver=[]
    if doc.custom_opration_approver:
        for i in doc.custom_opration_approver:
            app=frappe.get_doc("Department Approver",i)
            dep_approver.append(app.approver)
    dep_approver.append(doc.custom_department_head)
    # frappe.msgprint(str(dep_approver))
    return dep_approver
#this function for sales Reservation flow in find out pending qty
@frappe.whitelist()
def get_pending_qty(lineid, so_id):
    # frappe.msgprint(lineid)
    if lineid:
        data = frappe.db.sql("""
        SELECT 
            (soi.qty - COALESCE(SUM(dc.qty), 0) - COALESCE(SUM(sre.reserved_qty), 0)) AS pending_qty
        FROM 
            `tabSales Order` so 
        LEFT JOIN 
            `tabSales Order Item` AS soi ON soi.parent = so.name 
        LEFT JOIN 
            (SELECT 
                so_detail, 
                SUM(qty) AS qty 
            FROM 
                `tabDelivery Note Item` 
            GROUP BY 
                so_detail) AS dc ON dc.so_detail = soi.name 
        LEFT JOIN 
            (SELECT 
                voucher_detail_no, 
                SUM(reserved_qty) AS reserved_qty 
            FROM 
                `tabStock Reservation Entry` 
            WHERE 
                status NOT IN ('Delivered', 'Cancelled') 
            GROUP BY 
                voucher_detail_no) AS sre ON soi.name = sre.voucher_detail_no
        WHERE 
            (so.status != 'Completed' AND so.status != 'Cancelled') 
            AND soi.name = %s
            AND (soi.reserve_stock = 1 OR sre.voucher_detail_no IS NOT NULL)
        GROUP BY 
            soi.name
        """, (lineid,), as_dict=True)
        # frappe.msgprint(data)
        
        if data:
            return data[0]  # Return the first record if there is data
    else:
        return {'pending_qty': "Error"}  # Return a default value if no data is found


#this function for a create shipment from dc and sen a mail.
@frappe.whitelist()
def create_shipment(values, delivery_note_id):
    try:
        # Fetch the Delivery Note document
        dc = frappe.get_doc("Delivery Note", delivery_note_id)
        data_dict = json.loads(values)
        print(dc.set_warehouse)
        wm = frappe.db.sql("select warehouse_manager from `tabWarehouse Manager` where parent = %s",dc.set_warehouse,as_dict=True)
        cc_email=[]
        if wm:
            for i in wm:
                cc_email.append(i["warehouse_manager"])
        print(cc_email)
        # return w_nm

            
        # Create new Shipment document
        new_shipment = frappe.new_doc("Shipment")
        new_shipment.pickup_address_name = dc.dispatch_address_name
        new_shipment.delivery_address_name = dc.shipping_address_name
        new_shipment.delivery_to_type = "Customer"
        new_shipment.delivery_customer = dc.customer
        new_shipment.value_of_goods = dc.grand_total
        new_shipment.service_provider = data_dict.get("service_provider", "")
        new_shipment.awb_number = data_dict.get("awb_number", "")
        
        # Append Delivery Note and Parcel information
        new_shipment.append('shipment_delivery_note', {
            'delivery_note': delivery_note_id,
            'grand_total': dc.grand_total,
        })
        
        new_shipment.append('shipment_parcel', {
            'weight': 1,
            'count': dc.custom_number_of_count,
        })
        
        # Insert and submit the Shipment document
        new_shipment.insert()
        new_shipment.submit()
        frappe.db.commit()
        dc.custom_shipment_createed=1
        dc.save()
        frappe.db.commit()
        item_codes = []
        serial_no_condition = []
        for item in dc.items:
            if item.serial_and_batch_bundle:
                no = frappe.get_doc("Serial and Batch Bundle", item.serial_and_batch_bundle)
                serial_numbers = [sr_no.serial_no for sr_no in no.entries]
                serial_no_condition = serial_numbers
                item_codes.append({
                     'item_code': item.item_code,
                     'qty': item.qty,
                     'serial_no': serial_numbers,
                     'item_name':item.item_name
                })
        
        sale_person_email = frappe.db.get_value("Sales Person", dc.custom_sales_person, "custom_email")
        sender_details = frappe.db.get_value("Email Account", filters={'default_outgoing': 1}, fieldname=["name", "email_id"])
        sender = f"{sender_details[0]} <{sender_details[1]}>"
        
        so_id = next((i.against_sales_order for i in dc.items), "")
        po_no=frappe.db.get_value("Sales Order", so_id, "po_no")
        if po_no:
            if serial_no_condition:
                msg=f"""<p>We are pleased to inform you that your order [ Ref no {po_no} ] has been dispatched.</p><p>Below are the details of dispatch & Serial number for your reference.</p>"""
            else:
                msg=f"""<p>We are pleased to inform you that your order [ Ref no {po_no} ] has been dispatched.</p><p>Below are the details of dispatch.</p>"""
            
        else:
            if serial_no_condition:
                msg=f"""<p>We are pleased to inform you that your order has been dispatched.</p><p>Below are the details of dispatch & Serial number for your reference.</p>"""
            else:
                msg=f"""<p>We are pleased to inform you that your order has been dispatched to you.</p>"""        
        recipients = sale_person_email
        transaction_rows = ''.join(
        f'''
        <tr>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>{dc.posting_date}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>
            {detail.parent}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>
            {dc.custom_sales_invoice_no}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>
            {so_id}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>{dc.customer_name}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>{dc.shipping_address}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>{detail.item_name}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>{detail.qty}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>{data_dict.get("awb_number", "")}</td>
            <td style='border: 1px solid black;padding: 8px;text-align: left;'>{data_dict.get("service_provider", "")}</td>
        </tr>
        ''' for detail in dc.items
    )


        # Initialize batch_entries with placeholder data
        batch_entries = {}

        row_count = 0
       
        serial_number_rows = ""
        
        added_serial_numbers = set()

        for item in item_codes:
            if item['serial_no']:
                serial_number_rows += f"""<p><b>{item['item_code']} - {item['item_name']}</b></p>"""
                serial_number_rows += """<table style="border-collapse: collapse; width: 103%; margin-left: -11px; position: relative; top: -3px;"><tbody>"""
                for serial_no in item['serial_no']:
                    if serial_no not in added_serial_numbers:
                        added_serial_numbers.add(serial_no)
                        if row_count == 6:
                            row_count = 0
                        if row_count == 0:
                            serial_number_rows += "<tr>"    
                        serial_number_rows += f"""
                            <td colspan="2" style="color:black; padding:5px; border:1px solid black;">
                                <div style="display:flex; justify-content:space-between;">
                                    <div>{serial_no}</div>
                                </div>
                            </td>"""
                        
                        row_count += 1
                        if row_count == 6:
                            serial_number_rows += "</tr>"
                serial_number_rows += """</tbody></table>"""

        

        if serial_no_condition:

            message = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Shipment and DC Details</title>
                <style>
                    body {{
                        font-family: Verdana;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    .dc-details th {{
                        background-color: #d9ead3;
                    }}
                </style>
            </head>
            <body>
                <p>Dear Sir/Ma'am,</p>
                {msg}
                <br>
                <table>
                    <thead>
                        <tr>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Date</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>DC No</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Invoice No</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Sales Order</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Customer Name</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Destination</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Material Code</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Qty</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Docket No</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Courier Name</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transaction_rows}
                    </tbody>
                </table>
                <br><br>
                <p>Serial No Details</p><br>
                {serial_number_rows}
                <br>
                <p>Thank you for choosing us! we greatly appreciated your business and hope you enjoy your purchase.</p>
                <p>Please report any issue within 7 days of the delivery date, we may not be able to assist thereafter.</p>
                <p>In case of any queries or need further assistance for shipment/dispatch, please feel free to connect.</p>
                <div style="margin-left:25px">
                    <p><b>Email:</b> dispatch2@mantratec.com</p>
                    <p><b>Phone no:</b> +91 9512321029 </p>
                    <div style="margin-left:25px">
                    <p>Mantra Softech India Private Limited,</p>
                    <p>Shipping Address: LS No. 2376/1A 13501, Near Rainbow Company,</p>
                    <p>Jhulasan Road, Village-Rajpur, Taluka-Kadi,</p>
                    <p>Mahesana, Gujarat, India - 382705</p>
                    </div>
                </div>
                <p>We look forword to serving you again in the future.</p>
                <br>
                <p>Best Regards,</p>
                <p>Mantra Softrch India Private Limited</p>
            </body>
            </html>
            '''
            
        else:
            message = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Shipment and DC Details</title>
                <style>
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    body {{   
                        font-family: Verdana;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    .dc-details th {{
                        background-color: #d9ead3;
                    }}
                </style>
            </head>
            <body>
                <p>Dear Sir/Ma'am,</p>
                {msg}
                <br>
                <table>
                    <thead>
                        <tr>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Date</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>DC No</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Invoice No</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Sales Order</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Customer Name</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Destination</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Material Code</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Qty</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Docket No</th>
                            <th style='border: 1px solid black;padding: 8px;text-align: left;'>Courier Name</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transaction_rows}
                    </tbody>
                </table>
                <br><br>
                
                <p>Thank you for choosing us! we greatly appreciated your business and hope you enjoy your purchase.</p>
                <p>Please report any issue within 7 days of the delivery date, we may not be able to assist thereafter.</p>
                <p>In case of any queries or need further assistance for shipment/dispatch, please feel free to connect.</p>
                <div style="margin-left:25px">
                    <p><b>Email:</b> dispatch2@mantratec.com</p>
                    <p><b>Phone no:</b> +91 9512321029 </p>
                    <div style="margin-left:25px">
                    <p>Mantra Softech India Private Limited,</p>
                    <p>Shipping Address: LS No. 2376/1A 13501, Near Rainbow Company,</p>
                    <p>Jhulasan Road, Village-Rajpur, Taluka-Kadi,</p>
                    <p>Mahesana, Gujarat, India - 382705</p>
                    </div>
                </div>
                <p>We look forword to serving you again in the future.</p>
                <br>
                <p>Best Regards,</p>
                <p>Mantra Softech India Private Limited</p>
            </body>
            </html>
            '''
        
        # frappe.sendmail(
        #     recipients=recipients,
        #     cc=cc_email,
        #     subject=f"Dispatch Detail {dc.posting_date} - {dc.custom_sales_invoice_no} / {dc.customer_name}",
        #     message=message
        # )

        frappe.enqueue(
            'frappe.core.doctype.communication.email.make',
            sender=sender,
            recipients=recipients,
            cc=cc_email,
            subject=f"Dispatch Detail {dc.posting_date} - {dc.custom_sales_invoice_no} / {dc.customer_name}",
            content=message,
            send_email=True,
            now=True 
        )

        flush()
        frappe.local.response["message"] = "Done"
        return "Done"
    
    except Exception as e:
        frappe.log_error(message=str(e), title="Shipment Creation Error")
        return f"Error: {str(e)}"
    

@frappe.whitelist()
def login_to_avdm_scheduled():
    frappe.enqueue('mantra_dev.backend_code.api.login_to_avdm', queue='long', timeout=3600)     
    

@frappe.whitelist()
def login_to_avdm():
    if frappe.db.get_single_value("AVDM Setting", "enable") == 1:
            username = frappe.db.get_single_value("AVDM Setting", "username")
            password = frappe.db.get_single_value("AVDM Setting", "password")
            print(f"Password: {password}")  # For debugging; remove in production
            print(f"Username: {username}")

            login_url = "https://erptoavdm.aadhaardevice.com/ErptoAVDM/Login"
            login_headers = {
                "accept": "application/json",
            }
            login_body = {
                "username": username,
                "password": password
            }
        
        
            response = requests.post(login_url, headers=login_headers, json=login_body)
            print(f"Response: {response}")

            # Check if the response content is in bytes and decode it
            response_content = response.content
            if isinstance(response_content, bytes):
                response_content = response_content.decode('utf-8')
            
            print(f"Response Content: {response_content}")
            response_json = json.loads(response_content)
            print(f"Response JSON: {response_json}")
            details = response_json["details"]
            print(f"Details :{ details }")
            # details_json = json.loads(details)
            api_token = details["_APIToken"]
            print(f"API Token: {api_token}")
            
            creating_url = "https://erptoavdm.aadhaardevice.com/"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {api_token}"
            }
            body = []

            # login_body=[] /
            dc_list = frappe.get_list("Delivery Note", filters={"posting_date": nowdate(), "docstatus": 1})
            dc_response_json=''
            print(dc_list)
            for dc in dc_list:
                print(dc)
                dc_doc = frappe.get_doc("Delivery Note", dc)
                dc_item = dc_doc.items
                for i in dc_item:
                    if i.custom_abdm_enable == 1 and i.custom_reference_model_no:
                        if i.serial_no:
                            sr_no = i.serial_no
                            serial_no = sr_no.replace("\n", ",")
                            serial_no_list = serial_no.split(",")

                            for s_no in serial_no_list:
                                print(s_no)
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
            print(body)
            response1 = requests.post(creating_url, headers=headers, json=body)
            print(response1.status_code)
            if response1.status_code==200:
                print("ifff")
                dc_response_content = response1.content
                print(dc_response_content)
                if isinstance(dc_response_content, bytes):
                    dc_response_content = dc_response_content.decode('utf-8')
                    print(dc_response_content)
                print(f"Response Content: {dc_response_content}")
                dc_response_json = json.loads(dc_response_content)
                print(f"Response JSON: {dc_response_json}")
                
                
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

                    # Output the final result
                    print(result)
                    
                    for i in result:
                        for key, values in i.items():
                            # print(key, values)
                            for j in values:
                                if j in response_serial_no:
                                    frappe.db.set_value('Serial No', j, 'custom_marked_in_avdm', 1)
                                    
                                else:
                                    count = count + 1
                        if count == 0:
                            frappe.db.set_value('Delivery Note', key, 'custom_marked_in_avdm', 1)
                            # frappe.db.commit()
                        else:
                            pass
                    frappe.db.commit()
                
                
            else :
                print("else")
                dc_response_json=response1.status_code
            # dc_details = dc_response_json["details"]
            # print(f"Details :{ dc_details }")
            # details_json = json.loads(details)
            # dc_api_token = dc_details["_APIToken"]
            # print(f"API Token: {dc_api_token}")        
            # return body
            return dc_response_json 
            # return "jfgh", response_content
        
# @frappe.whitelist()
# def getl_serial_no():
#     creating_url = "http://192.168.6.111:5050/ErptoAVDM"
#     headers = {
#                 "accept": "application/json",
#                 "Authorization":"Bearer " + api_token
#             }
#     body = []
    
#     login_body=[]         
#     dc_list=frappe.get_list("Delivery Note",filters={"posting_date":"2024-08-06","docstatus":1})
#     for dc in dc_list:
#         dc_doc=frappe.get_doc("Delivery Note",dc)
#         dc_item=dc_doc.items
#         for i in dc_item:
#             if i.custom_abdm_enable==1:
#                 sr_no=i.serial_no
#                 serial_no=sr_no.replace("\n",",")
#                 for s_no in serial_no:
#                     data={
#                         "mastCode": 0,
#                         "serialNo": s_no,
#                         "custName": dc_doc.customer_name,
#                         "dcNo": dc,
#                         "dcDate": dc_doc.posting_date,
#                         "model": dc_doc.custom_reference_model_no ,  
#                         "subModelType": 0
#                     }
#                     body.append(data)
#     response = requests.post(creating_url, headers=headers, json=body)             
#     return serial_no