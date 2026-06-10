import frappe


LEGACY_TABLE = "`tabDATEV Settings`"


def execute():
	if not legacy_table_exists():
		return

	for row in get_legacy_rows():
		if frappe.db.exists("DATEV Configuration", row["name"]):
			continue

		if frappe.db.exists("DATEV Configuration", {"company": row["company"]}):
			continue

		doc = frappe.new_doc("DATEV Configuration")
		doc.update(row)
		doc.insert(ignore_permissions=True)


def legacy_table_exists():
	return bool(frappe.db.sql(f"show tables like 'tabDATEV Settings'"))


def get_legacy_rows():
	return frappe.db.sql(
		f"""
		select
			name,
			client as company,
			client_number,
			consultant,
			consultant_number,
			account_number_length,
			temporary_against_account_number,
			opening_against_account_number
		from {LEGACY_TABLE}
		where ifnull(client, '') != ''
		""",
		as_dict=True,
	)
