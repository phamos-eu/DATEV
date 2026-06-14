import importlib
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

class TestFixDatevReportModule(unittest.TestCase):
	def load_patch_module(self):
		sys.modules.setdefault("frappe", SimpleNamespace())
		module = importlib.import_module("datev.patches.post_model_sync.fix_datev_report_module")
		return importlib.reload(module)

	def test_execute_updates_stale_report_module(self):
		patch_module = self.load_patch_module()
		set_calls = []

		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(
				exists=lambda doctype, name: doctype == "Report" and name == "DATEV",
				get_value=lambda doctype, name, fieldname: "DATEV",
				set_value=lambda doctype, name, fieldname, value, update_modified=False: set_calls.append(
					(doctype, name, fieldname, value, update_modified)
				),
			)
		)

		with patch.object(patch_module, "frappe", fake_frappe):
			patch_module.execute()

		self.assertEqual(
			set_calls,
			[("Report", "DATEV", "module", "GB DATEV", False)],
		)

	def test_execute_skips_when_report_module_is_already_correct(self):
		patch_module = self.load_patch_module()
		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(
				exists=lambda doctype, name: doctype == "Report" and name == "DATEV",
				get_value=lambda doctype, name, fieldname: "GB DATEV",
				set_value=lambda *args, **kwargs: self.fail("set_value should not run"),
			)
		)

		with patch.object(patch_module, "frappe", fake_frappe):
			patch_module.execute()

	def test_execute_skips_when_report_is_missing(self):
		patch_module = self.load_patch_module()
		fake_frappe = SimpleNamespace(
			db=SimpleNamespace(
				exists=lambda doctype, name: False,
				get_value=lambda *args, **kwargs: self.fail("get_value should not run"),
				set_value=lambda *args, **kwargs: self.fail("set_value should not run"),
			)
		)

		with patch.object(patch_module, "frappe", fake_frappe):
			patch_module.execute()
