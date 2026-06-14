import importlib
import importlib.util
import unittest
from pathlib import Path


class TestDatevGbDatevCompatibility(unittest.TestCase):
	def test_legacy_tree_is_shim_only(self):
		legacy_root = Path("gaertnerei_berger")
		allowed_files = {
			Path("config/__init__.py"),
			Path("gb_datev/__init__.py"),
			Path("gb_datev/doctype/__init__.py"),
			Path("gb_datev/doctype/datev_configuration/__init__.py"),
			Path("gb_datev/doctype/datev_mapping/__init__.py"),
			Path("gb_datev/doctype/datev_mapping_field/__init__.py"),
			Path("gb_datev/doctype/datev_settings/__init__.py"),
			Path("gb_datev/doctype/datev_unternehmen_online_settings/__init__.py"),
			Path("gb_datev/doctype/datev_voucher_config/__init__.py"),
			Path("gb_datev/report/__init__.py"),
			Path("gb_datev/report/datev/__init__.py"),
			Path("patches/__init__.py"),
			Path("patches/post_model_sync/__init__.py"),
			Path("templates/__init__.py"),
			Path("templates/pages/__init__.py"),
			Path("utils/__init__.py"),
		}
		shim_directories = ("config", "gb_datev", "patches", "templates", "utils")
		unexpected_files = sorted(
			str(path.relative_to(legacy_root))
			for directory in shim_directories
			for path in (legacy_root / directory).rglob("*")
			if path.is_file()
			and "__pycache__" not in path.parts
			and path.relative_to(legacy_root) not in allowed_files
		)

		self.assertEqual(unexpected_files, [])

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

	def test_legacy_patches_file_no_longer_registers_runtime_patches(self):
		patches_file = Path("gaertnerei_berger/patches.txt").read_text()

		self.assertEqual(patches_file.strip(), "[pre_model_sync]\n\n[post_model_sync]")
