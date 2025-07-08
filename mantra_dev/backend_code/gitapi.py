import frappe # type: ignore
from frappe import _ # type: ignore


@frappe.whitelist(allow_guest=True)
def mantra_git_detail(company_name=None):
    reply={}
    reply['GIT_TOKEN'] = "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"
    reply['GIT_USERNAME'] = "mantraerp"
    reply['GIT_REPO'] = ""
    reply['GIT_BRANCH'] = "main"

    if company_name=="mantra":
        reply['GIT_REPO'] = "github.com/mantraerp/mantra.git"
    elif company_name=="mantra_dev":
        reply['GIT_REPO'] = "github.com/mantraerp/mantra_dev.git"


    return reply
