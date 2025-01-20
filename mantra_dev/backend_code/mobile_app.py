import frappe
from frappe import _
import traceback
import json
from mantra_dev.backend_code.globle import errorLog,errorLogExites



#To return url
@frappe.whitelist(allow_guest=True)
def mobile_company_list(**kwargs):

	parameters=frappe._dict(kwargs)
 
	company_list= []
 
	company1={}
	company1['title']="Mantra"
	company1['url']="https://mantratec.milaap.ai"
	company_list.append(company1)
	
	company2={}
	company2['title']="Mefron"
	company2['url']="https://mefron.milaap.ai"
	company_list.append(company2)
	return company_list