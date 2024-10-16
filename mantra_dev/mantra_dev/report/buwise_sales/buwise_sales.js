frappe.query_reports["BUwise Sales"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: getFinancialYearStartDate(),
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: getFinancialYearEndDate(),
    },
  ],
};

function getFinancialYearStartDate() {
  var today = new Date();
  var fiscalYearStartMonth = 3; // April
  var fiscalYearStartYear = today.getMonth() < fiscalYearStartMonth ? today.getFullYear() - 1 : today.getFullYear();
  return new Date(fiscalYearStartYear, fiscalYearStartMonth - 1, 1); // Months are 0-based index
}

function getFinancialYearEndDate() {
  var today = new Date();
  var fiscalYearEndMonth = 2; // March
  var fiscalYearEndYear = today.getMonth() >= fiscalYearEndMonth ? today.getFullYear() + 1 : today.getFullYear();
  return new Date(fiscalYearEndYear, fiscalYearEndMonth + 1, 0); // Last day of March is the end of the financial year
}


