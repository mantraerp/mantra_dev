app_name = "mantra_dev"
app_title = "Mantra Dev"
app_publisher = "Foram Shah"
app_description = "Mantra Dev"
app_email = "foram@sanskartechnolab.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/mantra_dev/css/mantra_dev.css"
app_include_css = "bank_reconciliation_mantra.bundle.css"
app_include_js = [
    "/assets/mantra_dev/js/email_button.js",
    "/assets/mantra_dev/js/workflow.js",
    ]


# include js, css files in header of web template
# web_include_css = "/assets/mantra_dev/css/mantra_dev.css"
# web_include_js = "/assets/mantra_dev/js/mantra_dev.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "mantra_dev/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Material Request": "public/js/material_request_changes.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Payment Entry": "public/js/payment_entry.js",
    "Purchase Invoice": "public/js/purchase_invoce.js",
    "Subcontracting Receipt": "public/js/subcontracting_receipt.js",
    "Subcontracting Order": "public/js/subcontracting_order.js",
    "Journal Entry": "public/js/journal_entry.js",
    "Purchase Receipt": "public/js/purchase_receipt.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Tax Category": "public/js/tax_category.js",
    "Payment Request": "public/js/payment_request.js",
    "Sales Order": "public/js/sales_order.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Employee": "public/js/employee.js",
    # "Delivery Note": "public/js/delivery_note.js",
}
# doctype_js=  {"Sales Invoice" : "public/js/sales_invoice.js"}

doctype_list_js = {"Material Request" : "public/js/material_request.js","Payment Entry": "public/js/payment_entry.js","Delivery Note": "public/js/delivery_note.js",}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "mantra_dev/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "mantra_dev.utils.jinja_methods",
# 	"filters": "mantra_dev.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "mantra_dev.install.before_install"
# after_install = "mantra_dev.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "mantra_dev.uninstall.before_uninstall"
# after_uninstall = "mantra_dev.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "mantra_dev.utils.before_app_install"
# after_app_install = "mantra_dev.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "mantra_dev.utils.before_app_uninstall"
# after_app_uninstall = "mantra_dev.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mantra_dev.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Override standard doctype classes

# override_doctype_class = {
# 	"Sales Order": "mantra_dev.backend_code.sales_orders.sales_orders.SalesOrder"
# }



override_doctype_class = {
	# "Purchase Invoice": "mantra_dev.purchase_invoice.PurchaseInvoice",
    # "Purchase Receipt": "mantra_dev.purchase_receipt.PurchaseReceipt",
    "Material Request": "mantra_dev.material_request.MaterialRequest",
    "Subcontracting Order": "mantra_dev.backend_code.subcontracting.subcontracting_order.SubcontractingOrder",
    "Stock Reservation Entry": "mantra_dev.backend_code.stock_reservation_entry.stock_reservation_entry.StockReservationEntry",
    "Bank Transaction": "mantra_dev.overrides.bank_transaction.CustomBankTransaction"

}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # "Sales Invoice": {
    #     "on_submit": "mantra_dev.backend_code.sales_invoice.sales_invoice.make_dc"
    # },
    # "Delivery Note": {
    #     "on_update": "mantra_dev.backend_code.delivery_note.delivery_note.update_darft_delivered_qty",
    #     "on_insert": "mantra_dev.backend_code.delivery_note.delivery_note.update_darft_delivered_qty",
    #     "on_submit": "mantra_dev.backend_code.delivery_note.delivery_note.set_darft_delivered_qty",
    #     "on_trash":"mantra_dev.backend_code.delivery_note.delivery_note.set_darft_delivered_qty",
    # },
    # # "Subcontracting Receipt": {
    #     "before_submit": "mantra_dev.backend_code.subcontracting.subcontracting_receipt.make_stock_entry"
    # }
    "Bank Transaction": {
		"on_update_after_submit": "mantra_dev.overrides.bank_transaction.on_update_after_submit",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"bank": {
        # This may be used for predefined frequencies if they fit your needs
        "0/5 * * * *": [
            "mantra_dev.api_code.banck_transaction.get_icici_bank_file"
        ]
    },
    
    "cron": {
        "30 23 * * *": [
            "mantra_dev.backend_code.api.login_to_avdm_scheduled"
        ]
    },
 
    # "avdm": {
    #     "0/5 * * * *": [
    #         "mantra_dev.backend_code.api.login_to_avdm"
    #     ]
    # }
# 	"daily": [
# 		"mantra_dev.tasks.daily"
# 	],
# 	"hourly": [
# 		"mantra_dev.tasks.hourly"
# 	],
# 	"weekly": [
# 		"mantra_dev.tasks.weekly"
# 	],
# 	"monthly": [
# 		"mantra_dev.tasks.monthly"
# 	],
}

# Testing
# -------

# before_tests = "mantra_dev.install.before_tests"

# Overriding Methods
# ------------------------------
#
# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.selling.doctype.sales_order.sales_order.create_stock_reservation_entries":"mantra_dev.backend_code.sales_orders.sales_orders.create_stock_reservation_entries"
}

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "mantra_dev.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["mantra_dev.utils.before_request"]
# after_request = ["mantra_dev.utils.after_request"]

# Job Events
# ----------
# before_job = ["mantra_dev.utils.before_job"]
# after_job = ["mantra_dev.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"mantra_dev.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
    {"dt": "Report", "filters": [["module", "in", ["Mantra Dev"]]]},
    # {"dt": "Print Format", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Server Script", "filters": [["module", "in", ["Mantra Dev"]]]},
    # {"dt": "Client Script", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Property Setter", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Custom DocPerm",},
    {"dt": "Role",},
]


get_matching_queries = "mantra_dev.mantra_dev.doctype.bank_reconciliation_tool_mantra.bank_reconciliation_tool_mantra.get_matching_queries"