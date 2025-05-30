app_name = "mantra_dev"
app_title = "Mantra Dev"
app_publisher = "Mantra"
app_description = "Mantra Dev"
app_email = "info@mantratec.com"
app_license = "mit"
# required_apps = []


app_include_css = "bank_reconciliation_mantra.bundle.css"
app_include_js = [
    "/assets/mantra_dev/js/email_button.js",
    "/assets/mantra_dev/js/workflow.js",
    ]


# include js in doctype views
doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
    # "Bank Account": "public/js/bank_account.js",
    # "Expense Claim": "public/js/expense_claim.js",
}

# Override standard doctype classes
override_doctype_class = {
    "Subcontracting Order": "mantra_dev.backend_code.subcontracting.subcontracting_order.SubcontractingOrder",
    "Stock Reservation Entry": "mantra_dev.backend_code.stock_reservation_entry.stock_reservation_entry.StockReservationEntry",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
   
}

# Scheduled Tasks
# ---------------

scheduler_events = {

    "cron": {
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
    {"dt": "Role",},
]


# get_matching_queries = "mantra_dev.mantra_dev.doctype.bank_reconciliation_tool_mantra.bank_reconciliation_tool_mantra.get_matching_queries"
# get_matching_queries = "mantra.mantra.doctype.bank_reconciliation_tool_mantra.bank_reconciliation_tool_mantra.get_matching_queries"