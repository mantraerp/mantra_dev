import frappe
from frappe import _
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
from frappe.model.mapper import get_mapped_doc


# frappe.whitelist()
# def stop_print_in_draft(doc, method, x):    
#     if doc.docstatus == 0:  # Draft state
#         frappe.throw("You cannot print the Delivery Note in Draft state.")
#mantra


# @frappe.whitelist()
# def share_item_with_user(item_code, user_email):
#     """
#     Share an item with a specific user with read rights.
    
#     :param item_code: The item code of the Item to share
#     :param user_email: The email ID of the user to share the Item with
#     """
#     try:
#         # Use the Frappe Share API to share the document
#         frappe.share.add(
#             doctype="Item",  # Doctype to share
#             name=item_code,  # Name of the document (Item code)
#             user=user_email, # Email ID of the user
#             read=1,          # Grant Read access
#             write=0,         # Do not grant Write access
#             share=0          # Do not grant Share access
#         )
#         # frappe.msgprint(f"Item {item_code} shared with {user_email} successfully.")
#         return f"Item {item_code} shared with {user_email} successfully."
#     except Exception as e:
#         frappe.log_error(message=str(e), title="Error Sharing Item")
#         frappe.throw(f"Failed to share item {item_code} with {user_email}. Please check the error log.")




# @frappe.whitelist()
# def check():
#     target_dir=""
#     doc = frappe.get_doc('Bank Integration', 'Mantra - ICICI Bank Limited - 018951000027')
#     target_dir = doc.beneficiary_file_upload_path
#     print(target_dir)




@frappe.whitelist(allow_guest=True)
def mantra_git_pull(url):
    os.popen('sh {}'.format(url))
    return "Git pull run"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull_migrate():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git_migrate.sh')
    return "Git pull run with build"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull_export_fixture():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git_export_fixture.sh')
    return "Git pull run with export fixture"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull_bench_build_erpnext():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git_build_erpnext.sh')
    return "Git pull run with bench build errpnext"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull_bench_build_frappe():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git_build_frappe.sh')
    return "Git pull run with bench build frappe"