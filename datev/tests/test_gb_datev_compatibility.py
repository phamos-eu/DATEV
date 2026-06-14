import importlib
import importlib.util
import unittest
from pathlib import Path


class TestDatevGbDatevCompatibility(unittest.TestCase):
	def test_legacy_shim_uses_canonical_package_path(self):
		wrapper = importlib.import_module("gaertnerei_berger.gb_datev")
		target = importlib.import_module("datev.gb_datev")

		self.assertEqual(list(wrapper.__path__), list(target.__path__))

	def test_canonical_datev_configuration_module_spec_is_discoverable(self):
		spec = importlib.util.find_spec("datev.gb_datev.doctype.datev_configuration.datev_configuration")

		self.assertIsNotNone(spec)
		self.assertTrue(spec.origin.endswith("datev/gb_datev/doctype/datev_configuration/datev_configuration.py"))

	def test_legacy_datev_configuration_module_spec_resolves_to_canonical_tree(self):
		spec = importlib.util.find_spec(
			"gaertnerei_berger.gb_datev.doctype.datev_configuration.datev_configuration"
		)

		self.assertIsNotNone(spec)
		self.assertTrue(spec.origin.endswith("datev/gb_datev/doctype/datev_configuration/datev_configuration.py"))

	def test_canonical_datev_report_module_spec_is_discoverable(self):
		spec = importlib.util.find_spec("datev.gb_datev.report.datev.datev")

		self.assertIsNotNone(spec)
		self.assertTrue(spec.origin.endswith("datev/gb_datev/report/datev/datev.py"))

	def test_legacy_datev_report_module_spec_resolves_to_canonical_tree(self):
		spec = importlib.util.find_spec("gaertnerei_berger.gb_datev.report.datev.datev")

		self.assertIsNotNone(spec)
		self.assertTrue(spec.origin.endswith("datev/gb_datev/report/datev/datev.py"))

	def test_datev_report_js_uses_installed_app_method_path(self):
		report_js = Path("datev/gb_datev/report/datev/datev.js").read_text()

		self.assertIn("datev.gb_datev.report.datev.datev.download_datev_csv", report_js)
		self.assertNotIn("gaertnerei_berger.gb_datev.report.datev.datev.download_datev_csv", report_js)

	def test_datev_mapping_js_uses_installed_app_method_path(self):
		mapping_js = Path("datev/gb_datev/doctype/datev_mapping/datev_mapping.js").read_text()

		self.assertIn(
			"datev.gb_datev.doctype.datev_mapping.datev_mapping.get_map_to_field_options",
			mapping_js,
		)
		self.assertNotIn(
			"gaertnerei_berger.gb_datev.doctype.datev_mapping.datev_mapping.get_map_to_field_options",
			mapping_js,
		)
