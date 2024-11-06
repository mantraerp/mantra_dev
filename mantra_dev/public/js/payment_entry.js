frappe.ui.form.on("Payment Entry", {


  before_save(frm) {
    if (!frm.doc.mode_of_payment) {

    }
    else {
      if (frm.doc.status === 'Draft' && !frm.doc.mode_of_payment.includes('H2H')) {
        frm.set_value('custom_unique_batch_number', 'Not Available');
      }
      else {
        frm.set_value('custom_unique_batch_number')
      }
    }
  },


  onload: function (frm) {
    // Set query for party_bank_account after 1 second
    setTimeout(() => {
      frm.set_query("party_bank_account", () => {
        return {
          filters: {
            is_company_account: 0,
            party_type: frm.doc.party_type,
            party: frm.doc.party,
            workflow_state: "Approved",
          },
        };
      });
    }, 1000);
  },
  after_workflow_action: function (frm) {
    if (frm.doc.workflow_state == "Approved") {
      console.log("on_submit function called");
      frm.set_value("custom_approved_by", frappe.session.user)
      frm.update()
      frm.save()

    }
  }
});

frappe.listview_settings["Payment Entry"] = {
  refresh: function (listview) {
    $(".layout-side-section").hide();

  },
  onload: function (listview) {
    if (frappe.user.has_role("Make Payment")) {
      listview.page.add_inner_button(__("Make Payment"), function () {
        // Fetch current user's mobile number
        // const current_user = frappe.session.user;
        // frappe.call({
        //     method: 'frappe.client.get',
        //     args: {
        //         doctype: 'User',
        //         name: current_user
        //     },
        //     callback: function(r) {
        //         if (r.message && r.message.mobile_no) {
        //             const user_mobile = r.message.mobile_no;

        // Dialog to select bank account
        showBankAccountDialog();
        //         }
        //     }
        // });
      });
    }
  },
};

function showBankAccountDialog() {
  let d = new frappe.ui.Dialog({
    title: "Select Bank Account",
    fields: [
      {
        label: "Bank",
        fieldname: "bank",
        fieldtype: "Link",
        options: "Bank",
        reqd: 1,
      },
      {
        label: "Bank Account",
        fieldname: "bank_account",
        fieldtype: "Link",
        options: "Bank Integration",
        reqd: 1,
        get_query: () => {
          return {
            filters: [
              ["bank", "=", d.get_value("bank")],
              ["payments", "=", 1],
              ["enabled", "=", 1],
            ],
          };
        },
      },
    ],
    size: "small",
    primary_action_label: "Submit",
    primary_action: function (values) {
      d.hide();
      sendOTP(values.bank_account);
    },
  });

  d.show();
}

function sendOTP(bank_account) {
  frappe.call({
    method: "mantra_dev.api_code.banck_transaction.send_otp",
    args: {
      email: frappe.session.user,
    },
    callback: function (r) {
      if (r.message) {
        showOTPDIalog(bank_account);
      }
    },
  });
}

function showOTPDIalog(bank_account) {
  let d1 = new frappe.ui.Dialog({
    title: "Enter OTP",
    fields: [
      {
        label: "OTP",
        fieldname: "otp",
        fieldtype: "Data",
        reqd: 1,
      },
    ],
    size: "small",
    primary_action_label: "Submit",
    primary_action: function (values) {
      d1.hide();
      verifyotp(values.otp, bank_account);
      // selectPaymentEntry(bank_account);
    },
  });

  d1.show();
}
function verifyotp(otp, bank_account) {
  frappe.call({
    method: "mantra_dev.api_code.banck_transaction.verify_otp",
    args: {
      email: frappe.session.user,
      otp: otp,
    },
    callback: function (r) {
      if (r.message) {
        if (r.message == "Done") {
          // console.log("ngjnj c fngjg ");
          selectPaymentEntry(bank_account);
        }
        if (r.message == "Error") {
          // console.log("ngjnj c fngjg ");
          frappe.throw("Verifivation Code Is Incorrect, Please Ckeck & Enter")
        }
        if (r.message == "Expired") {
          // console.log("ngjnj c fngjg ");
          frappe.throw("Verifivation Code Is Expired, Plese Retry Process")
        }
      }
    },
  });
}
function selectPaymentEntry(bank_account) {
  console.log("Seclect payment Entry")
  frappe.call({
    method: "mantra_dev.api_code.banck_transaction.select_payment_entry",
    args: {
      bank_account: bank_account,
    },
    callback: function (r) {
      if (r.message) {
        console.log(r.message)

        frappe.call({
          method: "mantra_dev.api_code.banck_transaction.upload_file",
          args: {
            payment_entry_list: r.message.payment_entry_list,
            bank_account: bank_account,
          },
          callback: function (r) {
            if (r.message) {
              if (r.message == "Done") {
                // location.reload()
                window.open("https://cibnext.icicibank.com/corp/AuthenticationController?FORMSGROUP_ID__=AuthenticationFG&__START_TRAN_FLAG__=Y&FG_BUTTONS__=LOAD&ACTION.LOAD=Y&AuthenticationFG.LOGIN_FLAG=1&BANK_ID=ICI&ITM=nli_corp_primer_login_btn_desk", "_blank");
              }
              else {
                // window.location.reload()
              }




            }
          },
        });
        // frappe.msgprint(__('Payment entry selected successfully.'));
      }
    },
  });
}
