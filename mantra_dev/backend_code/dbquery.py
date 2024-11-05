import frappe
from frappe import _
from frappe.exceptions import QueryDeadlockError, QueryTimeoutError
from frappe.model.document import Document
from frappe.utils import cint, get_link_to_form, get_weekday, now, nowtime
from frappe.utils.user import get_users_with_role
from rq.timeouts import JobTimeoutException
from frappe.utils.background_jobs import get_jobs

import erpnext
from erpnext.accounts.utils import get_future_stock_vouchers, repost_gle_for_stock_vouchers
import traceback





@frappe.whitelist(allow_guest=True)
def update_warehouse_serial_no(serial_no,warehouse,item_code):
    
	reply={}
	reply["message"]="Update sucessfully."
	reply["status_code"]="200"
	reply["data"]=[]

	try:
		# query = "UPDATE `tabSerial No` SET `warehouse`='{}' WHERE `item_code`='{}' AND `name`='{}'".format(warehouse,item_code,serial_no)
		query = "UPDATE `tabSerial No` SET warehouse='{}' WHERE item_code='{}' AND name='{}'".format(warehouse,item_code,serial_no)
		frappe.db.sql(query)
		frappe.db.commit()
		return reply
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["error"]=str(e)
		reply["message"]=str(e)
		reply["error1"]=traceback.format_exc()
		return reply