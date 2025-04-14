from frappe.utils import getdate  # type: ignore
import frappe # type: ignore
#before overrides due_dates return string 
# due_dates = [d.due_date for d in self.get("payment_schedule") if d.due_date]

def set_due_date(self):
    #after ovrrides get in date format
    due_dates = [getdate(d.due_date) for d in self.get("payment_schedule") if d.due_date]
    if due_dates:
        self.due_date = max(due_dates)