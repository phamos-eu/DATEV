# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from datev.patches.post_model_sync import (
	migrate_datev_settings_to_configuration as migration,
	rename_datev_configuration_to_company as rename_migration,
)


class FakeDatevConfigurationDoc:
	def __init__(self, on_insert):
		self.values = {}
		self._on_insert = on_insert

	def update(self, values):
		self.values.update(values)

	def insert(self, ignore_permissions=False):
		self._on_insert(self.values.copy(), ignore_permissions)


class TestDATEVConfiguration(unittest.TestCase):
	def test_execute_migrates_legacy_rows_once_and_preserves_values(self):
		legacy_rows = [
			{
				"name": "old-datev-settings-row",
				"company": "_Test GmbH",
				"client_number": "12345",
				"consultant": "_Test Supplier",
				"consultant_number": "67890",
				"account_number_length": 4,
				"temporary_against_account_number": "9090",
				"opening_against_account_number": "9000",
			}
		]
		existing_companies = set()
		inserted_rows = []

		def fake_exists(doctype, filters):
			self.assertEqual(doctype, "DATEV Configuration")
			if isinstance(filters, dict):
				return filters.get("company") in existing_companies

			return False

		def on_insert(values, ignore_permissions):
			inserted_rows.append((values, ignore_permissions))
			existing_companies.add(values["company"])

		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(exists=fake_exists),
			new_doc=lambda doctype: (
				self.assertEqual(doctype, "DATEV Configuration")
				or FakeDatevConfigurationDoc(on_insert)
			),
		)

		with patch.object(migration, "frappe", fake_frappe), patch.object(
			migration, "legacy_table_exists", return_value=True
		), patch.object(migration, "get_legacy_rows", return_value=legacy_rows):
			migration.execute()
			migration.execute()

		self.assertEqual(len(inserted_rows), 1)

		inserted_values, ignore_permissions = inserted_rows[0]
		self.assertTrue(ignore_permissions)
		self.assertEqual(inserted_values, legacy_rows[0])

	def test_execute_skips_when_legacy_table_is_missing(self):
		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(exists=lambda *args, **kwargs: self.fail("exists should not run")),
			new_doc=lambda *args, **kwargs: self.fail("new_doc should not run"),
		)

		with patch.object(migration, "frappe", fake_frappe), patch.object(
			migration, "legacy_table_exists", return_value=False
		), patch.object(migration, "get_legacy_rows", side_effect=AssertionError("rows should not load")):
			migration.execute()


class TestRenameDATEVConfiguration(unittest.TestCase):
	def test_execute_renames_legacy_named_rows_to_company(self):
		rows = [
			SimpleNamespace(name="DATEV Settings", company="_Test GmbH"),
			SimpleNamespace(name="_Already Correct GmbH", company="_Already Correct GmbH"),
			SimpleNamespace(name="Other Legacy Name", company="_Existing Target GmbH"),
		]
		renamed = []

		def fake_exists(doctype, name):
			self.assertEqual(doctype, "DATEV Configuration")
			return name == "_Existing Target GmbH"

		fake_frappe = SimpleNamespace(
			get_all=lambda doctype, fields: (
				self.assertEqual(doctype, "DATEV Configuration") or self.assertEqual(fields, ["name", "company"]) or rows
			),
			db=SimpleNamespace(exists=fake_exists),
		)

		with patch.object(rename_migration, "frappe", fake_frappe), patch.object(
			rename_migration, "rename_doc", side_effect=lambda *args, **kwargs: renamed.append((args, kwargs))
		):
			rename_migration.execute()

		self.assertEqual(
			renamed,
			[
				(
					("DATEV Configuration", "DATEV Settings", "_Test GmbH"),
					{"force": True, "ignore_permissions": True},
				)
			],
		)
