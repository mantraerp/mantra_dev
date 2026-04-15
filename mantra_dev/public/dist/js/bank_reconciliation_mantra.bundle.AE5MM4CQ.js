(() => {
  var __defProp = Object.defineProperty;
  var __defProps = Object.defineProperties;
  var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
  var __getOwnPropSymbols = Object.getOwnPropertySymbols;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __propIsEnum = Object.prototype.propertyIsEnumerable;
  var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
  var __spreadValues = (a, b) => {
    for (var prop in b || (b = {}))
      if (__hasOwnProp.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    if (__getOwnPropSymbols)
      for (var prop of __getOwnPropSymbols(b)) {
        if (__propIsEnum.call(b, prop))
          __defNormalProp(a, prop, b[prop]);
      }
    return a;
  };
  var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));

  // ../mantra_dev/mantra_dev/public/js/bank_reconciliation_mantra/panel_manager.js
  frappe.provide("erpnext.accounts.bank_reconciliation");
  erpnext.accounts.bank_reconciliation.PanelManager = class PanelManager {
    constructor(opts) {
      Object.assign(this, opts);
      this.make();
    }
    make() {
      this.init_panels();
    }
    async init_panels() {
      this.transactions = await this.get_bank_transactions();
      this.$wrapper.empty();
      this.$panel_wrapper = this.$wrapper.append(`
			<div class="panel-container d-flex"></div>
		`).find(".panel-container");
      this.render_panels();
    }
    async get_bank_transactions() {
      let transactions = await frappe.call({
        method: "mantra_dev.mantra_dev.doctype.bank_reconciliation_tool_mantra.bank_reconciliation_tool_mantra.get_bank_transactions",
        args: {
          bank_account: this.doc.bank_account,
          from_date: this.doc.bank_statement_from_date,
          to_date: this.doc.bank_statement_to_date,
          order_by: this.order || "date asc"
        },
        freeze: true,
        freeze_message: __("Fetching Bank Transactions")
      }).then((response) => response.message);
      return transactions;
    }
    render_panels() {
      this.set_actions_panel_default_states();
      if (!this.transactions || !this.transactions.length) {
        this.render_no_transactions();
      } else {
        this.render_list_panel();
        let first_transaction = this.transactions[0];
        this.$list_container.find("#" + first_transaction.name).click();
      }
    }
    set_actions_panel_default_states() {
      this.actions_tab = "match_voucher-tab";
      this.actions_filters = {
        payment_entry: 0,
        journal_entry: 0,
        purchase_invoice: 1,
        sales_invoice: 1,
        loan_repayment: 0,
        loan_disbursement: 0,
        expense_claim: 0,
        bank_transaction: 0,
        exact_match: 0,
        exact_party_match: 0,
        unpaid_invoices: 1
      };
    }
    render_no_transactions() {
      this.$panel_wrapper.empty();
      this.$panel_wrapper.append(`
			<div class="no-transactions">
				<img src="/assets/frappe/images/ui-states/list-empty-state.svg" alt="Empty State">
				<p>${__("No Transactions found for the current filters.")}</p>
			</div>
		`);
    }
    render_list_panel() {
      this.$panel_wrapper.append(`
			<div class="list-panel">
				<div class="sort-by"></div>
				<div class="list-container"></div>
			</div>
		`);
      this.render_sort_area();
      this.render_transactions_list();
    }
    render_actions_panel() {
      this.actions_panel = new erpnext.accounts.bank_reconciliation.ActionsPanelManager({
        $wrapper: this.$panel_wrapper,
        transaction: this.active_transaction,
        doc: this.doc,
        panel_manager: this
      });
    }
    render_sort_area() {
      this.$sort_area = this.$panel_wrapper.find(".sort-by");
      this.$sort_area.append(`
			<div class="sort-by-title"> ${__("Sort By")} </div>
			<div class="sort-by-selector p-10"></div>
		`);
      var me = this;
      new frappe.ui.SortSelector({
        parent: me.$sort_area.find(".sort-by-selector"),
        args: {
          sort_by: me.order_by || "date",
          sort_order: me.order_direction || "asc",
          options: [
            { fieldname: "date", label: __("Date") },
            { fieldname: "withdrawal", label: __("Withdrawal") },
            { fieldname: "deposit", label: __("Deposit") },
            { fieldname: "unallocated_amount", label: __("Unallocated Amount") }
          ]
        },
        change: function(sort_by, sort_order) {
          me.order_by = sort_by || me.order_by || "date";
          me.order_direction = sort_order || me.order_direction || "asc";
          me.order = me.order_by + " " + me.order_direction;
          me.init_panels();
        }
      });
    }
    render_transactions_list() {
      this.$list_container = this.$panel_wrapper.find(".list-container");
      this.transactions.map((transaction) => {
        let amount = transaction.deposit || transaction.withdrawal;
        let symbol = transaction.withdrawal ? "-" : "+";
        let $row = this.$list_container.append(`
				<div id="${transaction.name}" class="transaction-row p-10">
					<!-- Date & Amount -->
					<div class="d-flex">
						<div class="w-50">
							<span title="${__("Date")}">${frappe.format(transaction.date, { fieldtype: "Date" })}</span>
						</div>

						<div class="w-50 bt-amount-contianer">
							<span
								title="${__("Amount")}"
								class="bt-amount ${transaction.withdrawal ? "text-danger" : "text-success"}"
							>
								<b>${symbol} ${format_currency(amount, transaction.currency)}</b>
							</span>
						</div>
					</div>


					<!-- Description, Reference, Party -->
					<div
						title="${__("Account Holder")}"
						class="account-holder ${transaction.bank_party_name ? "" : "hide"}"
					>
						<span class="account-holder-value">${transaction.bank_party_name}</span>
					</div>

					<div
						title="${__("Description")}"
						class="description ${transaction.description ? "" : "hide"}"
					>
						<span class="description-value">${transaction.description}</span>
					</div>

					<div
						title="${__("Reference")}"
						class="reference ${transaction.reference_number ? "" : "hide"}"
					>
						<span class="reference-value">${transaction.reference_number}</span>
					</div>
				</div>
			`).find("#" + transaction.name);
        $row.on("click", () => {
          $row.addClass("active").siblings().removeClass("active");
          this.active_transaction = this.transactions.find(({ name }) => name === transaction.name);
          this.render_actions_panel();
        });
      });
    }
    refresh_transaction(updated_amount = null, reference_number = null, party_type = null, party = null) {
      let id = this.active_transaction.name;
      let current_index = this.transactions.findIndex(({ name }) => name === id);
      let $current_transaction = this.$list_container.find("#" + id);
      let transaction = this.transactions[current_index];
      if (updated_amount) {
        this.transactions[current_index]["unallocated_amount"] = updated_amount;
      } else {
        this.transactions[current_index] = __spreadProps(__spreadValues({}, transaction), {
          reference_number,
          party_type,
          party
        });
        $current_transaction.find(".reference").removeClass("hide");
        $current_transaction.find(".reference-value").text(reference_number || "--");
      }
      $current_transaction.click();
    }
    move_to_next_transaction() {
      let id = this.active_transaction.name;
      let $current_transaction = this.$list_container.find("#" + id);
      let current_index = this.transactions.findIndex(({ name }) => name === id);
      let next_transaction = this.transactions[current_index + 1];
      let previous_transaction = this.transactions[current_index - 1];
      if (next_transaction) {
        this.active_transaction = next_transaction;
        let $next_transaction = $current_transaction.next();
        $next_transaction.click();
      } else if (previous_transaction) {
        this.active_transaction = previous_transaction;
        let $previous_transaction = $current_transaction.prev();
        $previous_transaction.click();
      }
      this.transactions.splice(current_index, 1);
      $current_transaction.remove();
      if (!next_transaction && !previous_transaction) {
        this.active_transaction = null;
        this.render_no_transactions();
      }
    }
  };

  // ../mantra_dev/mantra_dev/public/js/bank_reconciliation_mantra/actions_panel/actions_panel_manager.js
  frappe.provide("erpnext.accounts.bank_reconciliation");
  erpnext.accounts.bank_reconciliation.ActionsPanelManager = class ActionsPanelManager {
    constructor(opts) {
      Object.assign(this, opts);
      this.make();
    }
    make() {
      this.init_actions_container();
      this.render_tabs();
      this.$actions_container.find("#" + this.panel_manager.actions_tab).trigger("click");
    }
    init_actions_container() {
      if (this.$wrapper.find(".actions-panel").length > 0) {
        this.$actions_container = this.$wrapper.find(".actions-panel");
        this.$actions_container.empty();
      } else {
        this.$actions_container = this.$wrapper.append(`
				<div class="actions-panel"></div>
			`).find(".actions-panel");
      }
      this.$actions_container.append(`
			<div class="form-tabs-list">
				<ul class="nav form-tabs" role="tablist" aria-label="Action Tabs">
				</ul>
			</div>

			<div class="tab-content p-10"></div>
		`);
    }
    render_tabs() {
      this.tabs_list_ul = this.$actions_container.find(".form-tabs");
      this.$tab_content = this.$actions_container.find(".tab-content");
      frappe.realtime.off("doc_update");
      ["Details", "Match Voucher", "Create Voucher"].forEach((tab) => {
        let tab_name = frappe.scrub(tab);
        this.add_tab(tab_name, tab);
        let $tab_link = this.tabs_list_ul.find(`#${tab_name}-tab`);
        $tab_link.on("click", () => {
          this.$tab_content.empty();
          if (tab == "Details") {
            new erpnext.accounts.bank_reconciliation.DetailsTab({
              actions_panel: this,
              transaction: this.transaction,
              panel_manager: this.panel_manager
            });
          } else if (tab == "Match Voucher") {
            new erpnext.accounts.bank_reconciliation.MatchTab({
              actions_panel: this,
              transaction: this.transaction,
              panel_manager: this.panel_manager,
              doc: this.doc
            });
          } else {
            new erpnext.accounts.bank_reconciliation.CreateTab({
              actions_panel: this,
              transaction: this.transaction,
              panel_manager: this.panel_manager,
              company: this.doc.company
            });
          }
        });
      });
    }
    add_tab(tab_name, tab) {
      this.tabs_list_ul.append(`
			<li class="nav-item">
				<a class="nav-actions-link"
					id="${tab_name}-tab" data-toggle="tab"
					href="#" role="tab" aria-controls="${tab}"
				>
					${__(tab)}
				</a>
			</li>
		`);
    }
    after_transaction_reconcile(message, with_new_voucher = false, document_type) {
      let doc = message;
      let unallocated_amount = flt(doc.unallocated_amount);
      if (unallocated_amount > 0) {
        frappe.show_alert({
          message: __(
            "Bank Transaction {0} Partially {1}",
            [this.transaction.name, with_new_voucher ? "Reconciled" : "Matched"]
          ),
          indicator: "blue"
        });
        this.panel_manager.refresh_transaction(unallocated_amount);
      } else {
        let alert_string = __("Bank Transaction {0} Matched", [this.transaction.name]);
        if (with_new_voucher) {
          alert_string = __("Bank Transaction {0} reconciled with a new {1}", [this.transaction.name, document_type]);
        }
        frappe.show_alert({ message: alert_string, indicator: "green" });
        this.panel_manager.move_to_next_transaction();
      }
    }
  };

  // ../mantra_dev/mantra_dev/public/js/bank_reconciliation_mantra/actions_panel/create_tab.js
  frappe.provide("erpnext.accounts.bank_reconciliation");
  erpnext.accounts.bank_reconciliation.CreateTab = class CreateTab {
    constructor(opts) {
      Object.assign(this, opts);
      this.make();
    }
    make() {
      this.panel_manager.actions_tab = "create_voucher-tab";
      this.create_field_group = new frappe.ui.FieldGroup({
        fields: this.get_create_tab_fields(),
        body: this.actions_panel.$tab_content,
        card_layout: true
      });
      this.create_field_group.make();
    }
    create_voucher() {
      var me = this;
      let values = this.create_field_group.get_values();
      let document_type = values.document_type;
      this.create_voucher_bts(
        false,
        (message) => me.actions_panel.after_transaction_reconcile(
          message,
          true,
          document_type
        )
      );
    }
    edit_in_full_page() {
      this.create_voucher_bts(true, (message) => {
        const doc = frappe.model.sync(message);
        let doctype = doc[0].doctype, docname = doc[0].name;
        frappe.socketio.doc_subscribe(doctype, docname);
        frappe.realtime.off("doc_update");
        frappe.realtime.on("doc_update", (data) => {
          if (data.doctype === doctype && data.name === docname) {
            this.reconcile_new_voucher(doctype, docname);
          }
        });
        frappe.open_in_new_tab = true;
        frappe.set_route("Form", doctype, docname);
      });
    }
    create_voucher_bts(allow_edit = false, success_callback) {
      let values = this.create_field_group.get_values();
      let document_type = values.document_type;
      let method = "mantra_dev.mantra_dev.doctype.bank_reconciliation_tool_mantra.bank_reconciliation_tool_mantra";
      let args = {
        bank_transaction_name: this.transaction.name,
        reference_number: values.reference_number,
        reference_date: values.reference_date,
        party_type: values.party_type,
        party: values.party,
        posting_date: values.posting_date,
        mode_of_payment: values.mode_of_payment,
        allow_edit
      };
      if (document_type === "Payment Entry") {
        method = method + ".create_payment_entry_bts";
        args = __spreadProps(__spreadValues({}, args), {
          project: values.project,
          cost_center: values.cost_center
        });
      } else {
        method = method + ".create_journal_entry_bts";
        args = __spreadProps(__spreadValues({}, args), {
          entry_type: values.journal_entry_type,
          second_account: values.second_account
        });
      }
      frappe.call({
        method,
        args,
        callback: (response) => {
          if (response.exc) {
            frappe.show_alert({
              message: __("Failed to create {0} against {1}", [document_type, this.transaction.name]),
              indicator: "red"
            });
            return;
          } else if (response.message) {
            success_callback(response.message);
          }
        }
      });
    }
    reconcile_new_voucher(doctype, docname) {
      var me = this;
      frappe.call({
        method: "mantra_dev.mantra_dev.doctype.bank_reconciliation_tool_mantra.bank_reconciliation_tool_mantra.reconcile_voucher",
        args: {
          transaction_name: this.transaction.name,
          amount: this.transaction.unallocated_amount,
          voucher_type: doctype,
          voucher_name: docname
        },
        callback: (response) => {
          if (response.exc) {
            frappe.show_alert({
              message: __("Failed to reconcile new {0} against {1}", [doctype, me.transaction.name]),
              indicator: "red"
            });
            return;
          } else if (response.message && Object.keys(response.message).length > 0) {
            if (response.message.deleted) {
              frappe.realtime.off("doc_update");
              return;
            }
            me.actions_panel.after_transaction_reconcile(
              response.message,
              true,
              doctype
            );
          }
        }
      });
    }
    get_create_tab_fields() {
      let party_type = this.transaction.party_type || (flt(this.transaction.withdrawal) > 0 ? "Supplier" : "Customer");
      return [
        {
          label: __("Document Type"),
          fieldname: "document_type",
          fieldtype: "Select",
          options: `Payment Entry
Journal Entry`,
          default: "Payment Entry",
          onchange: () => {
            let value = this.create_field_group.get_value("document_type");
            let fields = this.create_field_group;
            fields.get_field("party").df.reqd = value === "Payment Entry";
            fields.get_field("party_type").df.reqd = value === "Payment Entry";
            fields.get_field("journal_entry_type").df.reqd = value === "Journal Entry";
            fields.get_field("second_account").df.reqd = value === "Journal Entry";
            this.create_field_group.refresh();
          }
        },
        {
          fieldtype: "Section Break",
          fieldname: "details",
          label: "Details"
        },
        {
          fieldname: "reference_number",
          fieldtype: "Data",
          label: __("Reference Number"),
          default: this.transaction.reference_number || this.transaction.description ? this.transaction.description.slice(0, 140) : ""
        },
        {
          fieldname: "posting_date",
          fieldtype: "Date",
          label: __("Posting Date"),
          reqd: 1,
          default: this.transaction.date
        },
        {
          fieldname: "reference_date",
          fieldtype: "Date",
          label: __("Cheque/Reference Date"),
          reqd: 1,
          default: this.transaction.date
        },
        {
          fieldname: "mode_of_payment",
          fieldtype: "Link",
          label: __("Mode of Payment"),
          options: "Mode of Payment"
        },
        {
          fieldname: "edit_in_full_page",
          fieldtype: "Button",
          label: __("Edit in Full Page"),
          click: () => {
            this.edit_in_full_page();
          }
        },
        {
          fieldname: "column_break_7",
          fieldtype: "Column Break"
        },
        {
          label: __("Journal Entry Type"),
          fieldname: "journal_entry_type",
          fieldtype: "Select",
          options: `Bank Entry
Journal Entry
Inter Company Journal Entry
Cash Entry
Credit Card Entry
Debit Note
Credit Note
Contra Entry
Excise Entry
Write Off Entry
Opening Entry
Depreciation Entry
Exchange Rate Revaluation
Deferred Revenue
Deferred Expense`,
          default: "Bank Entry",
          depends_on: "eval: doc.document_type == 'Journal Entry'"
        },
        {
          fieldname: "second_account",
          fieldtype: "Link",
          label: "Account",
          options: "Account",
          get_query: () => {
            return {
              filters: {
                is_group: 0,
                company: this.company
              }
            };
          },
          depends_on: "eval: doc.document_type == 'Journal Entry'"
        },
        {
          fieldname: "party_type",
          fieldtype: "Link",
          label: "Party Type",
          options: "DocType",
          reqd: 1,
          default: party_type,
          get_query: function() {
            return {
              filters: {
                name: [
                  "in",
                  Object.keys(frappe.boot.party_account_types)
                ]
              }
            };
          },
          onchange: () => {
            let value = this.create_field_group.get_value("party_type");
            this.create_field_group.get_field("party").df.options = value;
          }
        },
        {
          fieldname: "party",
          fieldtype: "Link",
          label: "Party",
          default: this.transaction.party,
          options: party_type,
          reqd: 1
        },
        {
          fieldname: "project",
          fieldtype: "Link",
          label: "Project",
          options: "Project",
          depends_on: "eval: doc.document_type == 'Payment Entry'"
        },
        {
          fieldname: "cost_center",
          fieldtype: "Link",
          label: "Cost Center",
          options: "Cost Center",
          depends_on: "eval: doc.document_type == 'Payment Entry'"
        },
        {
          fieldtype: "Section Break"
        },
        {
          label: __("Hidden field for alignment"),
          fieldname: "hidden_field",
          fieldtype: "Data",
          hidden: 1
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Create"),
          fieldtype: "Button",
          primary: true,
          click: () => this.create_voucher()
        }
      ];
    }
  };

  // ../mantra_dev/mantra_dev/public/js/bank_reconciliation_mantra/actions_panel/details_tab.js
  frappe.provide("erpnext.accounts.bank_reconciliation");
  erpnext.accounts.bank_reconciliation.DetailsTab = class DetailsTab {
    constructor(opts) {
      $.extend(this, opts);
      this.make();
    }
    make() {
      this.panel_manager.actions_tab = "details-tab";
      this.details_field_group = new frappe.ui.FieldGroup({
        fields: this.get_detail_tab_fields(),
        body: this.actions_panel.$tab_content,
        card_layout: true
      });
      this.details_field_group.make();
    }
    update_bank_transaction() {
      var me = this;
      const reference_number = this.details_field_group.get_value("reference_number");
      const party = this.details_field_group.get_value("party");
      const party_type = this.details_field_group.get_value("party_type");
      let diff = ["reference_number", "party", "party_type"].some((field) => {
        return me.details_field_group.get_value(field) !== me.transaction[field];
      });
      if (!diff) {
        frappe.show_alert({ message: __("No changes to update"), indicator: "yellow" });
        return;
      }
      frappe.call({
        method: "erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.update_bank_transaction",
        args: {
          bank_transaction_name: me.transaction.name,
          reference_number,
          party_type,
          party
        },
        freeze: true,
        freeze_message: __("Updating ..."),
        callback: (response) => {
          if (response.exc) {
            frappe.show_alert(__("Failed to update {0}", [me.transaction.name]));
            return;
          }
          me.panel_manager.refresh_transaction(
            null,
            reference_number,
            party_type,
            party
          );
          frappe.show_alert(
            __("Bank Transaction {0} updated", [me.transaction.name])
          );
        }
      });
    }
    get_detail_tab_fields() {
      return [
        {
          label: __("ID"),
          fieldname: "name",
          fieldtype: "Link",
          options: "Bank Transaction",
          default: this.transaction.name,
          read_only: 1
        },
        {
          label: __("Date"),
          fieldname: "date",
          fieldtype: "Date",
          default: this.transaction.date,
          read_only: 1
        },
        {
          label: __("Deposit"),
          fieldname: "deposit",
          fieldtype: "Currency",
          default: this.transaction.deposit,
          read_only: 1
        },
        {
          label: __("Withdrawal"),
          fieldname: "withdrawal",
          fieldtype: "Currency",
          default: this.transaction.withdrawal,
          read_only: 1
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Description"),
          fieldname: "description",
          fieldtype: "Small Text",
          default: this.transaction.description,
          read_only: 1
        },
        {
          label: __("To Allocate"),
          fieldname: "unallocated_amount",
          fieldtype: "Currency",
          options: "account_currency",
          default: this.transaction.unallocated_amount,
          read_only: 1
        },
        {
          label: __("Currency"),
          fieldname: "account_currency",
          fieldtype: "Link",
          options: "Currency",
          read_only: 1,
          default: this.transaction.currency,
          hidden: 1
        },
        {
          label: __("Account Holder"),
          fieldname: "account",
          fieldtype: "Data",
          default: this.transaction.bank_party_name,
          read_only: 1,
          hidden: this.transaction.bank_party_name ? 0 : 1
        },
        {
          label: __("Party Account Number"),
          fieldname: "account_number",
          fieldtype: "Data",
          default: this.transaction.bank_party_account_number,
          read_only: 1,
          hidden: this.transaction.bank_party_account_number ? 0 : 1
        },
        {
          label: __("Party IBAN"),
          fieldname: "iban",
          fieldtype: "Data",
          default: this.transaction.bank_party_iban,
          read_only: 1,
          hidden: this.transaction.bank_party_iban ? 0 : 1
        },
        {
          label: __("Update"),
          fieldtype: "Section Break",
          fieldname: "update_section"
        },
        {
          label: __("Reference Number"),
          fieldname: "reference_number",
          fieldtype: "Data",
          default: this.transaction.reference_number
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Party Type"),
          fieldname: "party_type",
          fieldtype: "Link",
          options: "DocType",
          get_query: function() {
            return {
              filters: {
                name: [
                  "in",
                  Object.keys(frappe.boot.party_account_types)
                ]
              }
            };
          },
          onchange: () => {
            let value = this.details_field_group.get_value("party_type");
            this.details_field_group.get_field("party").df.options = value;
          },
          default: this.transaction.party_type || null
        },
        {
          label: __("Party"),
          fieldname: "party",
          fieldtype: "Link",
          default: this.transaction.party,
          options: this.transaction.party_type || null
        },
        {
          fieldtype: "Section Break"
        },
        {
          label: __("Hidden field for alignment"),
          fieldname: "hidden_field",
          fieldtype: "Data",
          hidden: 1
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Submit"),
          fieldname: "submit_transaction",
          fieldtype: "Button",
          primary: true,
          click: () => this.update_bank_transaction()
        }
      ];
    }
  };

  // ../mantra_dev/mantra_dev/public/js/bank_reconciliation_mantra/actions_panel/match_tab.js
  frappe.provide("erpnext.accounts.bank_reconciliation");
  erpnext.accounts.bank_reconciliation.MatchTab = class MatchTab {
    constructor(opts) {
      $.extend(this, opts);
      this.make();
    }
    async make() {
      this.panel_manager.actions_tab = "match_voucher-tab";
      this.match_field_group = new frappe.ui.FieldGroup({
        fields: this.get_match_tab_fields(),
        body: this.actions_panel.$tab_content,
        card_layout: true
      });
      this.match_field_group.make();
      this.summary_empty_state();
      await this.populate_matching_vouchers();
    }
    summary_empty_state() {
      let summary_field = this.match_field_group.get_field("transaction_amount_summary").$wrapper;
      summary_field.append(
        `<div class="report-summary reconciliation-summary" style="height: 90px;">
			</div>`
      );
    }
    async populate_matching_vouchers() {
      let filter_fields = this.match_field_group.get_values();
      let document_types = Object.keys(filter_fields).filter((field) => filter_fields[field] === 1);
      this.update_filters_in_state(document_types);
      let vouchers = await this.get_matching_vouchers(document_types);
      this.render_data_table(vouchers);
      let transaction_amount = this.transaction.withdrawal || this.transaction.deposit;
      this.render_transaction_amount_summary(
        flt(transaction_amount),
        flt(this.transaction.unallocated_amount),
        flt(this.transaction.unallocated_amount),
        this.transaction.currency
      );
    }
    update_filters_in_state(document_types) {
      Object.keys(this.panel_manager.actions_filters).map((key) => {
        let value = document_types.includes(key) ? 1 : 0;
        this.panel_manager.actions_filters[key] = value;
      });
    }
    async get_matching_vouchers(document_types) {
      let vouchers = await frappe.call({
        method: "mantra_dev.mantra_dev.doctype.bank_reconciliation_tool_mantra.bank_reconciliation_tool_mantra.get_linked_payments",
        args: {
          bank_transaction_name: this.transaction.name,
          document_types,
          from_date: this.doc.bank_statement_from_date,
          to_date: this.doc.bank_statement_to_date,
          filter_by_reference_date: this.doc.filter_by_reference_date,
          from_reference_date: this.doc.from_reference_date,
          to_reference_date: this.doc.to_reference_date
        }
      }).then((result) => result.message);
      return vouchers || [];
    }
    render_data_table(vouchers) {
      this.summary_data = {};
      let table_data = vouchers.map((row) => {
        return [
          {
            content: row.reference_date || row.posting_date,
            format: (value) => {
              return row.date_match ? value.bold() : value;
            }
          },
          {
            content: row.paid_amount,
            format: (value) => {
              let formatted_value = format_currency(value, row.currency);
              let match_condition = row.amount_match || row.unallocated_amount_match;
              return match_condition ? formatted_value.bold() : formatted_value;
            }
          },
          {
            content: row.reference_no || "",
            format: (value) => {
              let reference_match = row.reference_number_match || row.name_in_desc_match;
              return reference_match ? value.bold() : value;
            }
          },
          {
            content: row.party,
            format: (value) => {
              if (row.party_name) {
                frappe.utils.add_link_title(row.party_type, row.party, row.party_name);
              }
              let formatted_value = frappe.format(row.party, { fieldtype: "Link", options: row.party_type });
              return row.party_match ? formatted_value.bold() : formatted_value;
            }
          },
          {
            content: row.name,
            format: (value) => {
              return frappe.format(row.name, { fieldtype: "Link", options: row.doctype });
            },
            doctype: row.doctype
          }
        ];
      });
      const datatable_options = {
        columns: this.get_data_table_columns(),
        data: table_data,
        dynamicRowHeight: true,
        checkboxColumn: true,
        inlineFilters: true,
        layout: "fluid",
        serialNoColumn: false
      };
      this.actions_table = new frappe.DataTable(
        this.match_field_group.get_field("vouchers").$wrapper[0],
        datatable_options
      );
      this.actions_table.style.setStyle(
        ".dt-cell[data-row-index='0']",
        { backgroundColor: "#F4FAEE" }
      );
      this.bind_row_check_event();
    }
    bind_row_check_event() {
      $(this.actions_table.bodyScrollable).on("click", ".dt-cell__content input", (e) => {
        let idx = $(e.currentTarget).closest(".dt-cell").data().rowIndex;
        let voucher_row = this.actions_table.getRows()[idx];
        this.check_data_table_row(voucher_row);
      });
    }
    check_data_table_row(row) {
      if (!row)
        return;
      let id = row[5].content;
      let value = this.get_amount_from_row(row);
      if (id in this.summary_data) {
        delete this.summary_data[id];
      } else {
        this.summary_data[id] = value;
      }
      let total_allocated = Object.values(this.summary_data).reduce(
        (a, b) => a + b,
        0
      );
      let max_allocated = Math.min(total_allocated, this.transaction.unallocated_amount);
      let transaction_amount = this.transaction.withdrawal || this.transaction.deposit;
      let unallocated = flt(this.transaction.unallocated_amount) - flt(max_allocated);
      let actual_unallocated = flt(this.transaction.unallocated_amount) - flt(total_allocated);
      this.render_transaction_amount_summary(
        flt(transaction_amount),
        unallocated,
        actual_unallocated,
        this.transaction.currency
      );
    }
    render_transaction_amount_summary(total_amount, unallocated_amount, actual_unallocated, currency) {
      let summary_field = this.match_field_group.get_field("transaction_amount_summary").$wrapper;
      summary_field.empty();
      let allocated_amount = flt(total_amount) - flt(unallocated_amount);
      new erpnext.accounts.bank_reconciliation.SummaryCard({
        $wrapper: summary_field,
        values: {
          "Amount": [total_amount],
          "Allocated Amount": [allocated_amount, ""],
          "To Allocate": [
            unallocated_amount,
            unallocated_amount < 0 ? "text-danger" : unallocated_amount > 0 ? "text-blue" : "text-success",
            actual_unallocated
          ]
        },
        currency,
        wrapper_class: "reconciliation-summary"
      });
    }
    reconcile_selected_vouchers() {
      const me = this;
      let selected_vouchers = [];
      let selected_map = this.actions_table.rowmanager.checkMap;
      let voucher_rows = this.actions_table.getRows();
      selected_map.forEach((value, idx) => {
        if (value === 1) {
          let row = voucher_rows[idx];
          selected_vouchers.push({
            payment_doctype: row[5].doctype,
            payment_name: row[5].content,
            amount: this.get_amount_from_row(row)
          });
        }
      });
      if (!selected_vouchers.length > 0) {
        frappe.show_alert({
          message: __("Please select at least one voucher to reconcile"),
          indicator: "red"
        });
        return;
      }
      frappe.call({
        method: "erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.reconcile_vouchers",
        args: {
          bank_transaction_name: this.transaction.name,
          vouchers: selected_vouchers
        },
        freeze: true,
        freeze_message: __("Reconciling ..."),
        callback: (response) => {
          if (response.exc) {
            frappe.show_alert({
              message: __("Failed to reconcile {0}", [this.transaction.name]),
              indicator: "red"
            });
            return;
          }
          me.actions_panel.after_transaction_reconcile(response.message, false);
        }
      });
    }
    get_match_tab_fields() {
      const filters_state = this.panel_manager.actions_filters;
      return [
        {
          label: __("Payment Entry"),
          fieldname: "payment_entry",
          fieldtype: "Check",
          default: filters_state.payment_entry,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          label: __("Journal Entry"),
          fieldname: "journal_entry",
          fieldtype: "Check",
          default: filters_state.journal_entry,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Purchase Invoice"),
          fieldname: "purchase_invoice",
          fieldtype: "Check",
          default: filters_state.purchase_invoice,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          label: __("Sales Invoice"),
          fieldname: "sales_invoice",
          fieldtype: "Check",
          default: filters_state.sales_invoice,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Loan Repayment"),
          fieldname: "loan_repayment",
          fieldtype: "Check",
          default: filters_state.loan_repayment,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          label: __("Loan Disbursement"),
          fieldname: "loan_disbursement",
          fieldtype: "Check",
          default: filters_state.loan_disbursement,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Expense Claim"),
          fieldname: "expense_claim",
          fieldtype: "Check",
          default: filters_state.expense_claim,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          label: __("Bank Transaction"),
          fieldname: "bank_transaction",
          fieldtype: "Check",
          default: filters_state.bank_transaction,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          fieldtype: "Section Break"
        },
        {
          label: __("Show Exact Amount"),
          fieldname: "exact_match",
          fieldtype: "Check",
          default: filters_state.exact_match,
          onchange: () => {
            this.populate_matching_vouchers();
          }
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Show Exact Party"),
          fieldname: "exact_party_match",
          fieldtype: "Check",
          default: this.transaction.party_type && this.transaction.party ? 1 : 0,
          onchange: () => {
            this.populate_matching_vouchers();
          },
          read_only: !Boolean(this.transaction.party_type && this.transaction.party)
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Unpaid Vouchers"),
          fieldname: "unpaid_invoices",
          fieldtype: "Check",
          default: filters_state.unpaid_invoices,
          onchange: () => {
            this.populate_matching_vouchers();
          },
          depends_on: "eval: doc.sales_invoice || doc.purchase_invoice || doc.expense_claim"
        },
        {
          fieldtype: "Column Break"
        },
        {
          fieldtype: "Section Break"
        },
        {
          fieldname: "transaction_amount_summary",
          fieldtype: "HTML"
        },
        {
          fieldname: "vouchers",
          fieldtype: "HTML"
        },
        {
          fieldtype: "Section Break",
          fieldname: "section_break_reconcile",
          hide_border: 1
        },
        {
          label: __("Hidden field for alignment"),
          fieldname: "hidden_field_2",
          fieldtype: "Data",
          hidden: 1
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Reconcile"),
          fieldname: "bt_reconcile",
          fieldtype: "Button",
          primary: true,
          click: () => {
            this.reconcile_selected_vouchers();
          }
        }
      ];
    }
    get_data_table_columns() {
      return [
        {
          name: __("Date"),
          editable: false,
          format: (value) => {
            return frappe.format(value, { fieldtype: "Date" });
          }
        },
        {
          name: __("Outstanding"),
          editable: false
        },
        {
          name: __("Reference"),
          editable: false,
          align: "left"
        },
        {
          name: __("Party"),
          editable: false
        },
        {
          name: __("Voucher"),
          editable: false
        }
      ];
    }
    get_amount_from_row(row) {
      return row[2].content;
    }
  };

  // ../mantra_dev/mantra_dev/public/js/bank_reconciliation_mantra/summary_number_card.js
  frappe.provide("erpnext.accounts.bank_reconciliation");
  erpnext.accounts.bank_reconciliation.SummaryCard = class SummaryCard {
    constructor(opts) {
      Object.assign(this, opts);
      this.make();
    }
    make() {
      this.$wrapper.empty();
      let $container = null;
      if (this.$wrapper.find(".report-summary").length > 0) {
        $container = this.$wrapper.find(".report-summary");
        $container.empty();
      } else {
        $container = this.$wrapper.append(
          `<div class="report-summary ${this.wrapper_class || ""}"></div>`
        ).find(".report-summary");
      }
      Object.keys(this.values).map((key) => {
        let values = this.values[key];
        if (values[2] && values[2] !== values[0]) {
          let df = { fieldtype: "Currency", options: "currency" };
          let value_1 = frappe.format(
            values[0],
            df,
            { only_value: true },
            { currency: this.currency }
          );
          let value_2 = frappe.format(
            values[2],
            df,
            { only_value: true },
            { currency: this.currency }
          );
          let visible_value = `${value_1} (${value_2})`;
          var number_card = $(
            `<div class="summary-item">
						<div class="summary-label">${__(key)}</div>
						<div class="summary-value">${visible_value}</div>
					</div>`
          );
        } else {
          let data = {
            value: values[0],
            label: __(key),
            datatype: "Currency",
            currency: this.currency
          };
          var number_card = frappe.utils.build_summary_item(data);
        }
        $container.append(number_card);
        if (values.length > 1) {
          let $text = number_card.find(".summary-value");
          $text.addClass(values[1]);
        }
      });
    }
  };
})();
//# sourceMappingURL=bank_reconciliation_mantra.bundle.AE5MM4CQ.js.map
