import frappe


REPORT_NAME = "DATEV"
EXPECTED_MODULE = "GB DATEV"


def execute():
	if not frappe.db.exists("Report", REPORT_NAME):
		return

	current_module = frappe.db.get_value("Report", REPORT_NAME, "module")

	if current_module == EXPECTED_MODULE:
		return

	frappe.db.set_value("Report", REPORT_NAME, "module", EXPECTED_MODULE, update_modified=False)
