app_name = "mantra_dev"
app_title = "Mantra Dev"
app_publisher = "Mantra"
app_description = "Mantra Dev"
app_email = "info@mantratec.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ---------1------

# include js, css files in header of0 desk.html
# app_include_css = "/assets/mantra_dev/css/mantra_dev.css"
app_include_css = "bank_reconciliation_mantra.bundle.css"
app_include_js = [
    "/assets/mantra_dev/js/email_button.js",
    "/assets/mantra_dev/js/workflow.js",
    ]


# include js in doctype views
doctype_js = {
    "Stock Entry": "public/js/stock_entry.js",
    "Subcontracting Receipt": "public/js/subcontracting_receipt.js",
    "Subcontracting Order": "public/js/subcontracting_order.js",
    "Journal Entry": "public/js/journal_entry.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Tax Category": "public/js/tax_category.js",
    "Sales Order": "public/js/sales_order.js",
    # "Employee": "public/js/employee.js",
    "Bank Account": "public/js/bank_account.js",
    "Supplier": "public/js/supplier.js",
    "Quality Inspection": "public/js/quality_inspection.js",
    "Payroll Entry": "public/js/payroll_entry.js",
    # "Salary Slip": "public/js/salary_slip.js",
    "Project":"public/js/project.js",
    "Expense Claim": "public/js/expense_claim.js",
}
doctype_list_js = {
}


# Override standard doctype classes
override_doctype_class = {
    "Material Request": "mantra_dev.material_request.MaterialRequest",
    "Subcontracting Order": "mantra_dev.backend_code.subcontracting.subcontracting_order.SubcontractingOrder",
    "Stock Reservation Entry": "mantra_dev.backend_code.stock_reservation_entry.stock_reservation_entry.StockReservationEntry",
    "Bank Transaction": "mantra_dev.overrides.bank_transaction.CustomBankTransaction",
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
	},
    "Purchase Order": {
        "on_submit": "mantra_dev.backend_code.purchase_order.purchase_order.create_purchase_order_expected_date",
        "on_cancel": "mantra_dev.backend_code.purchase_order.purchase_order.cancel_purchase_order_expected_date"
    },
    "Purchase Receipt": {
        "on_submit": "mantra_dev.backend_code.purchase_receipt.purchase_receipt.update_purchase_order_expected_date",
        "on_cancel": "mantra_dev.backend_code.purchase_receipt.purchase_receipt.update_cancel_purchase_order_expected_date" 
    },
    "Purchase Invoice":{
        "on_update": "mantra_dev.purchase_invoice.override_validate_due_date",
    },
    "Stock Entry":{
        "on_submit":"mantra_dev.backend_code.qc_module.send_notification_on_submit",
        "on_cancel":"mantra_dev.backend_code.qc_module.revert_auto_transfer_stock",
        "on_trash": "mantra_dev.backend_code.qc_module.restore_qc_quantities_on_delete"
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {

    "cron": {
        "0/1 * * * *": [
            "mantra_dev.mantra_dev.doctype.minop_setting.minop_setting.url_cron_process"
        ],
        "0/2 * * * *": [
            "mantra_dev.backend_code.avdm.process_one_record"
        ],        
        "0/5 * * * *": [
            "mantra_dev.api_code.bank_transaction.get_icici_bank_file",
        ],
        "30 23 * * *": [
            "mantra_dev.backend_code.avdm.login_to_avdm_scheduled"
        ],
    },
}

override_whitelisted_methods = {
	"erpnext.selling.doctype.sales_order.sales_order.create_stock_reservation_entries":"mantra_dev.backend_code.sales_orders.sales_orders.create_stock_reservation_entries",
    # "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt":"mantra_dev.overrides.purchase_order.override_make_purchase_receipt",
    # "erpnext.setup.doctype.employee.employee.create_user":"mantra_dev.overrides.employee.create_user",
}


fixtures = [
    "Workflow",
    "Workflow State",
    "Workflow Action Master",
    "Letter Head",
    {"dt": "Report", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Print Format", "filters": [["module", "in", ["Mantra Dev"]]]},
    # {"dt": "Server Script", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Client Script", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Property Setter", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Custom DocPerm",},
    # {"dt": "Document Naming Rule"},
    {"dt": "Role",},
]


get_matching_queries = "mantra_dev.mantra_dev.doctype.bank_reconciliation_tool_mantra.bank_reconciliation_tool_mantra.get_matching_queries"
