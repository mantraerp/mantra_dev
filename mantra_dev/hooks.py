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
        "30 22 * * *": [
            "mantra_dev.backend_code.serialno.serial_no_scheduled"
        ],
        "30 23 * * *": [
            "mantra_dev.backend_code.avdm.login_to_avdm_scheduled"
        ],
    },
}

fixtures = [
    "Workflow",
    "Workflow State",
    "Workflow Action Master",
    "Letter Head",
    {"dt": "Report", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Print Format", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Client Script", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Property Setter", "filters": [["module", "in", ["Mantra Dev"]]]},
    {"dt": "Custom DocPerm",},
    {"dt": "Role",},
]