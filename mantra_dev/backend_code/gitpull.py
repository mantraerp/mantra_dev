import frappe
from frappe import _
import os





@frappe.whitelist(allow_guest=True)
def mantra_git_pull_with_url(url):
    os.popen('sh {}'.format(url))
    return "Git pull run"

@frappe.whitelist(allow_guest=True)
def mantra_git_pull(url):
    os.popen('sh /home/mantra/mantrastage-bench/ShellScript/mantra_git.sh')
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