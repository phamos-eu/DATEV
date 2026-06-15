import frappe


REPORT_DOCTYPE = "Report"
REPORT_NAME = "DATEV"
CURRENT_MODULE = "DATEV"
LEGACY_MODULES = {"GB DATEV", "gb_datev"}


def execute():
	if not frappe.db.exists(REPORT_DOCTYPE, REPORT_NAME):
		return

	module = frappe.db.get_value(REPORT_DOCTYPE, REPORT_NAME, "module")
	if module not in LEGACY_MODULES:
		return

	frappe.db.set_value(REPORT_DOCTYPE, REPORT_NAME, "module", CURRENT_MODULE, update_modified=False)
