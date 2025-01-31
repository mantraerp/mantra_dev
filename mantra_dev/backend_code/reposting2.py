import frappe
from frappe import _
from frappe.exceptions import QueryDeadlockError, QueryTimeoutError
from frappe.model.document import Document
from frappe.utils import cint, get_link_to_form, get_weekday, now, nowtime
from frappe.utils.user import get_users_with_role
from rq.timeouts import JobTimeoutException
from frappe.utils.background_jobs import get_jobs

import erpnext
import requests

from erpnext.accounts.utils import get_future_stock_vouchers, repost_gle_for_stock_vouchers
from erpnext.stock.stock_ledger import (
	get_affected_transactions,
	get_items_to_be_repost,
	repost_future_sle,
)

from mantra_dev.backend_code.globle import errorLog
from datetime import date, datetime, timedelta


RecoverableErrors = (JobTimeoutException, QueryDeadlockError, QueryTimeoutError)


class RepostItemValuation(Document):
	def validate(self):
		self.set_status(write=False)
		self.reset_field_values()
		self.set_company()

	def reset_field_values(self):
		if self.based_on == "Transaction":
			self.item_code = None
			self.warehouse = None

		self.allow_negative_stock = 1

	def set_company(self):
		if self.based_on == "Transaction":
			self.company = frappe.get_cached_value(self.voucher_type, self.voucher_no, "company")
		elif self.warehouse:
			self.company = frappe.get_cached_value("Warehouse", self.warehouse, "company")

	def set_status(self, status=None, write=True):
		status = status or self.status
		if not status:
			self.status = "Queued"
		else:
			self.status = status
		if write:
			self.db_set("status", self.status)

	def on_submit(self):
		"""During tests reposts are executed immediately.

		Exceptions:
		        1. "Repost Item Valuation" document has self.flags.dont_run_in_test
		        2. global flag frappe.flags.dont_execute_stock_reposts is set

		        These flags are useful for asserting real time behaviour like quantity updates.
		"""

		if not frappe.flags.in_test:
			return
		if self.flags.dont_run_in_test or frappe.flags.dont_execute_stock_reposts:
			return

		repost(self)

	def before_cancel(self):
		self.check_pending_repost_against_cancelled_transaction()

	def check_pending_repost_against_cancelled_transaction(self):
		if self.status not in ("Queued", "In Progress"):
			return

		if not (self.voucher_no and self.voucher_no):
			return

		transaction_status = frappe.db.get_value(self.voucher_type, self.voucher_no, "docstatus")
		if transaction_status == 2:
			msg = _("Cannot cancel as processing of cancelled documents is  pending.")
			msg += "<br>" + _("Please try again in an hour.")
			frappe.throw(msg, title=_("Pending processing"))

	@frappe.whitelist()
	def restart_reposting(self):
		self.set_status("Queued", write=False)
		self.current_index = 0
		self.distinct_item_and_warehouse = None
		self.items_to_be_repost = None
		self.gl_reposting_index = 0
		self.db_update()

	def deduplicate_similar_repost(self):
		"""Deduplicate similar reposts based on item-warehouse-posting combination."""
		if self.based_on != "Item and Warehouse":
			return

		filters = {
			"item_code": self.item_code,
			"warehouse": self.warehouse,
			"name": self.name,
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
		}

		frappe.db.sql(
			"""
			update `tabRepost Item Valuation`
			set status = 'Skipped'
			WHERE item_code = %(item_code)s
				and warehouse = %(warehouse)s
				and name != %(name)s
				and TIMESTAMP(posting_date, posting_time) > TIMESTAMP(%(posting_date)s, %(posting_time)s)
				and docstatus = 1
				and status = 'Queued'
				and based_on = 'Item and Warehouse'
				""",
			filters,
		)


def on_doctype_update():
	frappe.db.add_index("Repost Item Valuation", ["warehouse", "item_code"], "item_warehouse")


@frappe.whitelist(allow_guest=True)
def check_item_allownce(item_code):

	qty_allowance, over_billing_allowance = frappe.get_cached_value(
		"Item", item_code, ["over_delivery_receipt_allowance", "over_billing_allowance"]
	)
	return qty_allowance,over_billing_allowance



@frappe.whitelist(allow_guest=True)
def check_same_background_job(allow_guest=True):

	all_background_jobs = get_jobs()
	final_status = False
	for index, job in enumerate(all_background_jobs['mantratec.milaap.ai']):
		if str(job).startswith("<function repost_entries_single"):
			final_status = True
			break

	return final_status

@frappe.whitelist(allow_guest=True)
def get_background_job_list(allow_guest=True):

	return get_jobs()


@frappe.whitelist(allow_guest=True)
def repost_entries_single(doc_name,status):

	reply={}
	reply['message']=""
	reply['status_code']="200"

	if check_same_background_job():
		reply['status_code']="500"
		reply['message']="Already in loop"
		frappe.local.response['http_status_code'] = 500
		return reply

	doc = frappe.get_doc("Repost Item Valuation", doc_name)
	if doc.status == status:
		frappe.enqueue(repost,queue='long',job_name="Repost {}".format(doc_name),timeout=100000,doc=doc)
	else:
		frappe.local.response['http_status_code'] = 500
		reply['status_code']="500"
		reply['message']="Repost is not with pass status."
		return reply

	frappe.local.response['http_status_code'] = 200
	reply['message']="Job is schedule in background"
	return reply


@frappe.whitelist(allow_guest=True)
def repost(doc):
	try:
		frappe.flags.through_repost_item_valuation = True
		if not frappe.db.exists("Repost Item Valuation", doc.name):
			return

		# This is to avoid TooManyWritesError in case of large reposts
		frappe.db.MAX_WRITES_PER_TRANSACTION *= 6

		doc.set_status("In Progress")
		if not frappe.flags.in_test:
			frappe.db.commit()

		repost_sl_entries(doc)
		repost_gl_entries(doc)

		doc.set_status("Completed")
		doc.db_set("reposting_data_file", None)
		remove_attached_file(doc.name)

	except Exception as e:
		if frappe.flags.in_test:
			# Don't silently fail in tests,
			# there is no reason for reposts to fail in CI
			raise

		frappe.db.rollback()
		traceback = frappe.get_traceback(with_context=True)
		doc.log_error("Unable to repost item valuation")

		message = frappe.message_log.pop() if frappe.message_log else ""
		if isinstance(message, dict):
			message = message.get("message")

		status = "Failed"
		# If failed because of timeout, set status to In Progress
		if traceback and "timeout" in traceback.lower():
			status = "In Progress"

		if traceback:
			message += "<br><br>" + "<b>Traceback:</b> <br>" + traceback


		message = "{} <br><br> {}".format(message,str(traceback.format_exc()))

		# frappe.db.set_value(
		# 	doc.doctype,
		# 	doc.name,
		# 	{
		# 		"error_log": message,
		# 		"status": status,
		# 	},
		# )

		outgoing_email_account = frappe.get_cached_value(
			"Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"
		)

		if outgoing_email_account and not isinstance(e, RecoverableErrors):
			notify_error_to_stock_managers(doc, message)
			doc.set_status("Failed")
	finally:
		if not frappe.flags.in_test:
			frappe.db.commit()

def remove_attached_file(docname):
	if file_name := frappe.db.get_value(
		"File", {"attached_to_name": docname, "attached_to_doctype": "Repost Item Valuation"}, "name"
	):
		frappe.delete_doc("File", file_name, ignore_permissions=True, delete_permanently=True)








@frappe.whitelist(allow_guest=True)
def GLEntry_update():
	query = "UPDATE `tabGL Entry` SET `debit`='299.99', `debit_in_account_currency`='299.99' WHERE `name`='ACC-GLE-2024-25153'" 
	# query = "UPDATE `tabGL Entry` SET `debit`='0.01', `debit_in_account_currency`='0.01' WHERE `name`='ACC-GLE-2024-25155'" 

	test= frappe.db.sql(query,as_dict=1)
	frappe.db.commit()
	return True



@frappe.whitelist(allow_guest=True)
def repost_entries_query(query):

	if str(query.lower()).startswith("delete"):
		return "Delete query not perform"

	reply = {}
	# query = "SELECT name from `tabRepost Item Valuation` WHERE status in ('Queued', 'In Progress') and creation <= '{}' and creation >= '{}' and docstatus = 1 ORDER BY timestamp(posting_date, posting_time) asc, creation asc, status asc limit 100".format(now(),'2024-11-1 00:00:52.242515')
	# query = "SELECT creation from `tabRepost Item Valuation` WHERE status in ('Queued', 'In Progress') and creation >= '{}' and docstatus = 1 ORDER BY timestamp(posting_date, posting_time) asc, creation asc, status asc".format('2024-10-01 00:00:52.242515')

	reply['query']=query
	test= frappe.db.sql(query,as_dict=1)
	reply['data']=test
	reply['data_length']=len(test)

	return reply


@frappe.whitelist(allow_guest=True)
def repost_entries_without_voucher_no():

	reply = {}
 
	query_delete = "DELETE FROM `tabError Log` WHERE error='REPOSTING'"
	reply['delete_query']=query_delete
	test= frappe.db.sql(query_delete,as_dict=1)
 
	d = datetime.today()
	finalDate = d - timedelta(1)
 
	query = "SELECT * from `tabRepost Item Valuation` WHERE voucher_type IS NULL and status in ('Queued','Failed','In Progress') and posting_date>='2024-06-01' and posting_date<='{}' and docstatus = 1 ORDER BY timestamp(posting_date, posting_time) asc, creation asc, status asc".format(str(finalDate))
	reply['query']=query
	test= frappe.db.sql(query,as_dict=1)

	for row in test:
		errorLog(row['name'],'REPOSTING',True)

	reply['data']=test
	reply['data_length']=len(test)

	return reply

@frappe.whitelist(allow_guest=True)
def repost_entries_without_voucher_no_process_one_entry():

	reply={}
	query = "SELECT * from `tabError Log` WHERE error='{}' LIMIT 1".format('REPOSTING')
	records = frappe.db.sql(query,as_dict=1)
	reply['record_process']=records
	if len(records)!=0:
		doc = frappe.get_doc("Repost Item Valuation", records[0]['method'])
		reply['doc_process']=doc

		if doc.status not in ['Completed','Skipped']:
			reply['process_start_reposting']=doc.status
			# return repost(doc)
			frappe.enqueue(repost,queue='long',job_name="Repost {}".format(doc.name),timeout=100000,doc=doc)

		frappe.enqueue(delete_entry_from_error_log,queue='long',job_name="Delete Repost Entries {}".format(doc.name),timeout=100000,doc_name=doc.name)

	return reply

def delete_entry_from_error_log(doc_name):
	deleteQuery = "DELETE FROM `tabError Log` WHERE `method`='{}' AND `error`='REPOSTING'".format(doc_name)
	temp = frappe.db.sql(deleteQuery)
	return True


@frappe.whitelist(allow_guest=True)
def make_url_request_for_reposting():
	"""
	"mantra_dev.backend_code.reposting2.make_url_request_for_reposting"

	"""
	url = "http://192.168.1.38:8001/api/method/mantra_dev.backend_code.reposting2.repost_entries_without_voucher_no_process_one_entry"  # Replace with your target URL
	headers = {
		"Content-Type": "application/json",
	}
	try:
		# Make a GET request
		response = requests.get(url, headers=headers, timeout=10)
		
		# Check if the request was successful
		if response.status_code == 200:
			# Process the JSON response
			data = response.json()
			# frappe.msgprint(f"Response Data: {data}")
		else:
			errorLog("Single repost",f"Request failed with status code {response.status_code}: {response.text}",False)
			# frappe.throw(f"Request failed with status code {response.status_code}: {response.text}")

	except requests.exceptions.RequestException as e:
		# Log the exception and create an error log in ERPNext
		trace = frappe.get_traceback()
		errorLog("Single repost",str(trace),False,"Reposting")

		# frappe.log_error(trace, "URL Request Error")
		# frappe.throw(f"An error occurred: {str(e)}")




def repost_sl_entries(doc):
	if doc.based_on == "Transaction":
		repost_future_sle(
			voucher_type=doc.voucher_type,
			voucher_no=doc.voucher_no,
			allow_negative_stock=doc.allow_negative_stock,
			via_landed_cost_voucher=doc.via_landed_cost_voucher,
			doc=doc,
		)
	else:
		repost_future_sle(
			args=[
				frappe._dict(
					{
						"item_code": doc.item_code,
						"warehouse": doc.warehouse,
						"posting_date": doc.posting_date,
						"posting_time": doc.posting_time,
					}
				)
			],
			allow_negative_stock=doc.allow_negative_stock,
			via_landed_cost_voucher=doc.via_landed_cost_voucher,
			doc=doc,
		)


def repost_gl_entries(doc):
	if not cint(erpnext.is_perpetual_inventory_enabled(doc.company)):
		return

	# directly modified transactions
	directly_dependent_transactions = _get_directly_dependent_vouchers(doc)
	repost_affected_transaction = get_affected_transactions(doc)
	repost_gle_for_stock_vouchers(
		directly_dependent_transactions + list(repost_affected_transaction),
		doc.posting_date,
		doc.company,
		repost_doc=doc,
	)


def _get_directly_dependent_vouchers(doc):
	"""Get stock vouchers that are directly affected by reposting
	i.e. any one item-warehouse is present in the stock transaction"""

	items = set()
	warehouses = set()

	if doc.based_on == "Transaction":
		ref_doc = frappe.get_doc(doc.voucher_type, doc.voucher_no)
		doc_items, doc_warehouses = ref_doc.get_items_and_warehouses()
		items.update(doc_items)
		warehouses.update(doc_warehouses)

		sles = get_items_to_be_repost(doc.voucher_type, doc.voucher_no)
		sle_items = {sle.item_code for sle in sles}
		sle_warehouses = {sle.warehouse for sle in sles}
		items.update(sle_items)
		warehouses.update(sle_warehouses)
	else:
		items.add(doc.item_code)
		warehouses.add(doc.warehouse)

	affected_vouchers = get_future_stock_vouchers(
		posting_date=doc.posting_date,
		posting_time=doc.posting_time,
		for_warehouses=list(warehouses),
		for_items=list(items),
		company=doc.company,
	)
	return affected_vouchers


def notify_error_to_stock_managers(doc, traceback):
	recipients = get_users_with_role("Stock Manager")
	if not recipients:
		get_users_with_role("System Manager")

	recipients = ['ravi.patel@mantratec.com']
	subject = _("Error while reposting item valuation - UAT Cron")
	message = (
		_("Hi,")
		+ "<br>"
		+ _("An error has been appeared while reposting item valuation via {0}").format(
			get_link_to_form(doc.doctype, doc.name)
		)
		+ "<br>"
		+ _(
			"Please check the error message and take necessary actions to fix the error and then restart the reposting again."
		)
	)
	frappe.sendmail(recipients=recipients, subject=subject, message=message)