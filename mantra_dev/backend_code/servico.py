import frappe # type: ignore
from frappe import _ # type: ignore
from frappe.utils import nowdate # type: ignore
import json
import traceback
import requests # type: ignore
from mantra_dev.backend_code.globle import errorLog,errorLogExites # type: ignore
import ast

delivery_note_number_proccess = []
key_token = "TOKENAVDM"
key_body_process = "BODYPROCESSAVDM"
key_serial_no = "SERIALNOAVDM"
key_sub_serial_no = "SUBSERIALNO"
key_dc_no = "DCNOAVDM"
# email_send = False



# @frappe.whitelist(allow_guest=True)
@frappe.whitelist()
def servico_hook(**kwargs):

	#Authorization : 41fd63d8ae8ea1b:dbaef9936307497
	parameters=frappe._dict(kwargs)
	parameters['status_code']=200
	parameters['sucessfull']=True

	query = "SELECT * from `tabError Log` WHERE method='ServicoHook'"
	previous_log = frappe.db.sql(query,as_dict=1)
	if len(previous_log)<=50:
		errorLog("ServicoHook",str(parameters))

	return parameters