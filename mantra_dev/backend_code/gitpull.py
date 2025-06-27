import frappe
from frappe import _
import os



@frappe.whitelist(allow_guest=True)
def mantra_repo_git_push():
    os.popen('sh /home/mantra/scripts/git_push.sh')
    return "Mantra export customisation and git push"


@frappe.whitelist(allow_guest=True)
def mantra_dev_repo_git_push():
    os.popen('sh /home/mantra/scripts/git_push_mantra_dev.sh')
    return "Mantra dev export customisation and git push"







@frappe.whitelist(allow_guest=True)
def mantra_git_pull_with_url(url):
    os.popen('sh {}'.format(url))
    return "URL RUN: {}".format(url)

@frappe.whitelist(allow_guest=True)
def mantra_git_pull():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git.sh')
    return "Git pull run"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull_migrate():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git_migrate.sh')
    return "Migrate bench"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull_export_fixture():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git_export_fixture.sh')
    return "Export fixture > Git push run"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull_bench_build_erpnext():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git_build_erpnext.sh')
    return "Build ERPNext app"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull_bench_build_frappe():
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git_build_frappe.sh')
    return "Build frappe app"