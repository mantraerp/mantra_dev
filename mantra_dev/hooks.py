app_name = "mantra_dev"
app_title = "Mantra Dev"
app_publisher = "Foram Shah"
app_description = "Mantra Dev"
app_email = "foram@sanskartechnolab.com"
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
    "Bank Account": "public/js/bank_account.js",
    "Supplier": "public/js/supplier.js",
    "Quality Inspection": "public/js/quality_inspection.js",
    "Payroll Entry": "public/js/payroll_entry.js",
    "Item": "public/js/item.js",
    "Project":"public/js/project.js",
    "Expense Claim": "public/js/expense_claim.js",

    # "Delivery Note": "public/js/delivery_note.js",
}
doctype_list_js = {
    "Material Request" : "public/js/material_request.js",
    "Payment Entry": "public/js/payment_entry.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Item" : "public/js/item_list.js",
    "Purchase Order": "public/js/purchase_order_list.js",
    "Purchase Invoice": "public/js/purchase_invoice_list.js",

    
    }


# Override standard doctype classes
override_doctype_class = {
    "Material Request": "mantra_dev.material_request.MaterialRequest",
    "Subcontracting Order": "mantra_dev.backend_code.subcontracting.subcontracting_order.SubcontractingOrder",
    "Stock Reservation Entry": "mantra_dev.backend_code.stock_reservation_entry.stock_reservation_entry.StockReservationEntry",
    "Bank Transaction": "mantra_dev.overrides.bank_transaction.CustomBankTransaction",
    "Purchase Order":"mantra_dev.overrides.purchase_order.CustomPurchaseOrder",
    "Purchase Receipt":"mantra_dev.overrides.purchase_receipt.CustomPurchaseReceipt"
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
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {

    "cron": {
        "0/2 * * * *": [
            "mantra_dev.backend_code.avdm.process_one_record"
        ],        
        "0/5 * * * *": [
            "mantra_dev.api_code.banck_transaction.get_icici_bank_file",
        ],
        "30 23 * * *": [
            "mantra_dev.backend_code.avdm.login_to_avdm_scheduled"
        ],
        "0 8 * * *": [
            "mantra_dev.backend_code.minop.employee_remain_bank_account",
            "mantra_dev.backend_code.globle.check_system_status"
        ]
    },
	"daily": [
        #This log will clear beny process files log every day at night.
		"mantra_dev.backend_code.globle.clear_beny_file_process_log"
	],
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

override_whitelisted_methods = {
	"erpnext.selling.doctype.sales_order.sales_order.create_stock_reservation_entries":"mantra_dev.backend_code.sales_orders.sales_orders.create_stock_reservation_entries",
    #  "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt":"mantra_dev.overrides.purchase_order.override_make_purchase_receipt"

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
