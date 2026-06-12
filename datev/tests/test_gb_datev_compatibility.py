import unittest
from pathlib import Path


class TestDatevGbDatevCompatibility(unittest.TestCase):
	def test_datev_mapping_js_uses_installed_app_method_path(self):
		mapping_js = Path("datev/datev/doctype/datev_mapping/datev_mapping.js").read_text()

		self.assertIn(
			"datev.gb_datev.doctype.datev_mapping.datev_mapping.get_map_to_field_options",
			mapping_js,
		)
		self.assertNotIn(
			"datev.datev.doctype.datev_mapping.datev_mapping.get_map_to_field_options",
			mapping_js,
		)
