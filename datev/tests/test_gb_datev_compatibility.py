import importlib
import importlib.util
import unittest


class TestDatevGbDatevCompatibility(unittest.TestCase):
	def test_wrapper_uses_current_package_path(self):
		wrapper = importlib.import_module("datev.gb_datev")
		target = importlib.import_module("datev.datev")

		self.assertEqual(list(wrapper.__path__), list(target.__path__))

	def test_doctype_package_import_uses_current_package_path(self):
		wrapper = importlib.import_module("datev.gb_datev.doctype")
		target = importlib.import_module("datev.datev.doctype")

		self.assertEqual(list(wrapper.__path__), list(target.__path__))

	def test_report_package_import_uses_current_package_path(self):
		wrapper = importlib.import_module("datev.gb_datev.report")
		target = importlib.import_module("datev.datev.report")

		self.assertEqual(list(wrapper.__path__), list(target.__path__))

	def test_datev_configuration_module_spec_is_discoverable(self):
		spec = importlib.util.find_spec("datev.gb_datev.doctype.datev_configuration.datev_configuration")

		self.assertIsNotNone(spec)
		self.assertTrue(spec.origin.endswith("datev/datev/doctype/datev_configuration/datev_configuration.py"))

	def test_datev_report_module_spec_is_discoverable(self):
		spec = importlib.util.find_spec("datev.gb_datev.report.datev.datev")

		self.assertIsNotNone(spec)
		self.assertTrue(spec.origin.endswith("datev/datev/report/datev/datev.py"))
