frappe.ui.form.on("Payment Entry", {

  onload: function (frm) {

    if (frm.doc.party) 
    {
      if (frm.is_new()) 
      {
        frappe.call({
          method: "mantra_dev.backend_code.payment_entry.payment_entry_api.party_detail",
          args: {
            party: frm.doc.party,
            party_type: frm.doc.party_type,
          },
          callback: function (r) {
            if (r.message.status_code === 200) 
            {
              frm.set_value("party_bank_account", r.message.data[0]['name']);
              frm.set_value("contact_email", r.message.email);
            }
            else 
            {
              frm.set_value("party_bank_account", "");
              frappe.msgprint(r.message.message)
            }
          }
        });
      }
    } else {
      frm.set_value("party_bank_account", "")
    }

    if (frm.doc.mode_of_payment) 
    {
      if (frm.is_new()) {
        frappe.call({
          method: "mantra_dev.backend_code.payment_entry.payment_entry_api.company_bank_account_detail",
          args: {
            mode_of_payment: frm.doc.mode_of_payment
          },
          callback: function (r) {
            frm.set_value("bank_account", r.message);
          }
        });
      }
    } 
    else 
    {
      frm.set_value("bank_account", "")
    }

    // Set query for party_bank_account after 1 second
    setTimeout(() => {
      frm.set_query("party_bank_account", () => {
        return {
          filters: {
            is_company_account: 0,
            disabled: 0,
            party_type: frm.doc.party_type,
            party: frm.doc.party,
            workflow_state: "Approved",
          },
        };
      });
    }, 1000);
  },
  refresh: function (frm) {

  },
  before_save(frm) {

    if (frm.doc.mode_of_payment) {

      if (frm.doc.status === 'Draft' && !frm.doc.mode_of_payment.includes('H2H')) {
        frm.set_value('custom_unique_batch_number', 'Not Available');
      }
      else {
        frm.set_value('custom_unique_batch_number')
      }
    }
  },

  party(frm) {
    if (frm.doc.party) {
      frappe.call({
        method: "mantra_dev.backend_code.payment_entry.payment_entry_api.party_detail",
        args: {
          party: frm.doc.party,
          party_type: frm.doc.party_type,
        },
        callback: function (r) {
          if (r.message.status_code === 200) 
          {
            frm.set_value("party_bank_account", r.message.data[0]['name']);
            frm.set_value("contact_email", r.message.email);
          }
          else 
          {
            frm.set_value("party_bank_account", "");
            frappe.msgprint(r.message.message)
          }
        }
      });
    }
  },
  mode_of_payment(frm) {
    frappe.call({
      method: "mantra_dev.backend_code.payment_entry.payment_entry_api.company_bank_account_detail",
      args: {
        mode_of_payment: frm.doc.mode_of_payment
      },
      callback: function (r) {
        frm.set_value("bank_account", r.message);
      }
    });
  },
  after_workflow_action: function (frm) {

    if (frm.doc.workflow_state == "Approved") 
    {
      frm.set_value("custom_approved_by", frappe.session.user)
      frm.update()
      frm.save()
    }
  },
  before_workflow_action(frm) {

    // Validate to check bank account, party bank account and email(to send payment advice)
    if (frm.doc.workflow_state === 'Pending') {
      if (!frm.doc.bank_account) {
        frappe.dom.unfreeze();
        frappe.throw("Company bank account not found");
        return false;
      }
      if (String(frm.doc.bank_account) === "undefined") {
        frappe.dom.unfreeze();
        frappe.throw("Company bank account not found")
        return false;
      }

      if (!frm.doc.party_bank_account) {
        frappe.dom.unfreeze();
        frappe.throw("Party bank account not found");
        return false;
      }
      if (String(frm.doc.party_bank_account) === "undefined") {
        frappe.dom.unfreeze();
        frappe.throw("Party bank account not found")
        return false;
      }
      if (!frm.doc.contact_email) {
        frappe.dom.unfreeze();
        frappe.throw("Party email address not found");
        return false;
      }
      if (String(frm.doc.contact_email) === "undefined") {
        frappe.dom.unfreeze();
        frappe.throw("Party email address not found");
        return false;
      }
      if (String(frm.doc.contact_email) === "") {
        frappe.dom.unfreeze();
        frappe.throw("Party email address not found");
        return false;
      }
    }
  }
});

frappe.listview_settings["Payment Entry"] = {

  refresh: function (listview) {
    $(".layout-side-section").hide();
  },
  onload: function (listview) {
  },
};