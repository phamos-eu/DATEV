# Copyright (c) 2026, DATEV and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

VOUCHER_TYPE_OPTIONS = [
	"Sales Invoice",
	"Purchase Invoice",
	"Payment Entry",
	"Expense Claim",
	"Payroll Entry",
	"Bank Reconciliation",
	"Asset",
	"Stock Entry",
	"Journal Entry",
]

DATEV_REPORT_TYPES = [
	"EXTF_Buchungsstapel.csv",
	"EXTF_Kontenbeschriftungen.csv",
	"EXTF_Kunden.csv",
	"EXTF_Lieferanten.csv",
]

NON_VALUE_FIELD_TYPES = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"Fold",
	"Button",
	"HTML",
	"Table",
	"Table MultiSelect",
	"Heading",
	"Read Only",
	"Image",
	"Geolocation",
}


class DATEVMapping(Document):
	def validate(self):
		if not self.datev_configuration or not self.voucher_type:
			return

		existing_name = frappe.db.exists(
			"DATEV Mapping",
			{
				"datev_configuration": self.datev_configuration,
				"voucher_type": self.voucher_type,
				"name": ["!=", self.name or ""],
			},
		)
		if existing_name:
			frappe.throw(
				_("A DATEV Mapping already exists for voucher type {0} in configuration {1}.").format(
					self.voucher_type, self.datev_configuration
				)
			)


@frappe.whitelist()
def get_map_to_field_options(voucher_type: str) -> list[str]:
	"""Return `voucher.field` and `child_table.child_field` options for a voucher type."""
	if not voucher_type:
		return []

	meta = frappe.get_meta(voucher_type)
	options = []

	for field in meta.fields:
		if field.fieldtype in NON_VALUE_FIELD_TYPES:
			continue

		options.append(field.fieldname)

	for table_field in meta.fields:
		if table_field.fieldtype != "Table" or not table_field.options:
			continue

		child_meta = frappe.get_meta(table_field.options)
		for child_field in child_meta.fields:
			if child_field.fieldtype in NON_VALUE_FIELD_TYPES:
				continue
			options.append(f"{table_field.fieldname}.{child_field.fieldname}")

	return sorted(set(options))
