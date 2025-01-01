import frappe
from frappe import _
import os


@frappe.whitelist(allow_guest=True)
def mantra_git_pull_with_url(company_name):
    reply={}
    reply['password'] = "E&rp@_5546"
    reply['git_url'] = "https://mantraerp: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@github.com/mantraerp/mantra_dev.git"
    reply['company'] = company_name
    reply['GIT_USERNAME'] = "mantraerp"
    reply['GIT_PAT'] = "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"

    return reply