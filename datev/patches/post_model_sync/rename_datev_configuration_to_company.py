import frappe
from frappe.model.rename_doc import rename_doc


def execute():
	for row in frappe.get_all("DATEV Configuration", fields=["name", "company"]):
		if not row.company or row.name == row.company:
			continue

		if frappe.db.exists("DATEV Configuration", row.company):
			continue

		rename_doc(
			"DATEV Configuration",
			row.name,
			row.company,
			force=True,
			ignore_permissions=True,
		)
