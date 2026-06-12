import importlib
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class FakeDatevConfigurationDoc:
	def __init__(self, on_insert):
		self.values = {}
		self._on_insert = on_insert

	def update(self, values):
		self.values.update(values)

	def insert(self, ignore_permissions=False):
		self._on_insert(self.values.copy(), ignore_permissions)


class TestDATEVConfiguration(unittest.TestCase):
	def load_patch_module(self):
		sys.modules.setdefault("frappe", SimpleNamespace())
		module = importlib.import_module("datev.patches.post_model_sync.migrate_datev_settings_to_configuration")
		return importlib.reload(module)

	def test_execute_migrates_legacy_rows_once_and_preserves_values(self):
		migration = self.load_patch_module()
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
			self.assertTrue(ignore_permissions)
			inserted_rows.append(values)
			existing_companies.add(values["company"])

		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(
				sql=lambda query, as_dict=False: [object()] if "show tables like" in query else legacy_rows,
				exists=fake_exists,
			),
			new_doc=lambda doctype: FakeDatevConfigurationDoc(on_insert),
		)

		with patch.object(migration, "frappe", fake_frappe):
			migration.execute()
			migration.execute()

		self.assertEqual(
			inserted_rows,
			[
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
			],
		)

	def test_execute_skips_when_legacy_table_is_missing(self):
		migration = self.load_patch_module()
		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(
				sql=lambda query, as_dict=False: [],
				exists=lambda *args, **kwargs: self.fail("exists should not run"),
			),
			new_doc=lambda doctype: self.fail("new_doc should not run"),
		)

		with patch.object(migration, "frappe", fake_frappe):
			migration.execute()
