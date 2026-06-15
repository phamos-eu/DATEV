import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class TestEnforceCanonicalDatevReportModule(unittest.TestCase):
	def load_patch_module(self):
		sys.modules.setdefault("frappe", SimpleNamespace())
		module = importlib.import_module("datev.patches.post_model_sync.enforce_canonical_datev_report_module")
		return importlib.reload(module)

	def test_execute_rewrites_only_legacy_module_values(self):
		migration = self.load_patch_module()
		set_calls = []
		module_values = iter(["GB DATEV", "DATEV"])
		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(
				exists=lambda doctype, name: doctype == "Report" and name == "DATEV",
				get_value=lambda doctype, name, fieldname: (
					self.assertEqual((doctype, name, fieldname), ("Report", "DATEV", "module"))
					or next(module_values)
				),
				set_value=lambda doctype, name, fieldname, value, update_modified=False: set_calls.append(
					(doctype, name, fieldname, value, update_modified)
				),
			)
		)

		with patch.object(migration, "frappe", fake_frappe):
			migration.execute()
			migration.execute()

		self.assertEqual(
			set_calls,
			[("Report", "DATEV", "module", "DATEV", False)],
		)

	def test_execute_skips_when_report_is_missing(self):
		migration = self.load_patch_module()
		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(
				exists=lambda doctype, name: False,
				get_value=lambda *args, **kwargs: self.fail("get_value should not run"),
				set_value=lambda *args, **kwargs: self.fail("set_value should not run"),
			)
		)

		with patch.object(migration, "frappe", fake_frappe):
			migration.execute()

	def test_execute_skips_non_legacy_modules(self):
		migration = self.load_patch_module()
		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(
				exists=lambda doctype, name: True,
				get_value=lambda doctype, name, fieldname: "DATEV",
				set_value=lambda *args, **kwargs: self.fail("set_value should not run"),
			)
		)

		with patch.object(migration, "frappe", fake_frappe):
			migration.execute()

	def test_patches_txt_registers_replay_patch(self):
		patches_txt = Path(__file__).resolve().parents[1] / "patches.txt"
		patch_entries = patches_txt.read_text().splitlines()

		self.assertIn("datev.patches.post_model_sync.enforce_canonical_datev_report_module", patch_entries)

	def test_legacy_report_json_uses_canonical_module(self):
		report_json = (Path(__file__).resolve().parents[1] / "gb_datev" / "report" / "datev" / "datev.json").read_text()

		self.assertIn('"module": "DATEV"', report_json)
		self.assertNotIn('"module": "GB DATEV"', report_json)
