import frappe
from frappe import _
import traceback




@frappe.whitelist(allow_guest=True)
def errorLog(title,error,duplicate_check,reference_doctype=None,reference_name=None):


	if duplicate_check:
		query = "SELECT * from `tabError Log` WHERE error='{}' AND method='{}'".format(error,title)
		test= frappe.db.sql(query,as_dict=1)
		if len(test)!=0:
			return

	# Create a new Error Log document
	error_log = frappe.get_doc({
		"doctype": "Error Log",
		"error": error,
		"method": title,
	})
	# Insert the document into the database
	error_log.insert(ignore_permissions=True)

    #     print("Error Log created successfully!")
    # except Exception as e:
    #     # traceback.format_exc()
    #     print(f"Failed to create Error Log: {e}")

@frappe.whitelist(allow_guest=True)
def errorLogExites(title,error):
	query = "SELECT * from `tabError Log` WHERE error='{}' AND method='{}'".format(error,title)
	test= frappe.db.sql(query,as_dict=1)
	if len(test)!=0:
		return True

	return False

@frappe.whitelist(allow_guest=True)
def errorLogDelete(title,error):
	query = "DELETE FROM `tabError Log` WHERE error='{}' AND method='{}'".format(error,title)
	test= frappe.db.sql(query,as_dict=1)
	return "Record deleted"



@frappe.whitelist(allow_guest=True)
def ClearBenyFileProcessLog():
	query = "DELETE FROM `tabError Log` WHERE `method`='BENYPROCESSFILE'"
	test= frappe.db.sql(query,as_dict=1)
	return "Record deleted"