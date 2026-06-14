import importlib
import importlib.util
import unittest

from datev.tests._module_stubs import import_with_framework_stubs


class TestDatevDummyDataModule(unittest.TestCase):
	def test_dummy_data_module_spec_is_discoverable(self):
		spec = importlib.util.find_spec("datev.gb_datev.report.datev.datev_dummy_data")

		self.assertIsNotNone(spec)
		self.assertTrue(
			spec.origin.endswith("datev/gb_datev/report/datev/datev_dummy_data.py")
		)

	def test_seed_filters_use_fixed_dummy_window(self):
		module = import_with_framework_stubs("datev.gb_datev.report.datev.datev_dummy_data")

		self.assertEqual(
			module.get_seed_filters(),
			{
				"company": "DATEV Dummy GmbH",
				"from_date": "2026-01-01",
				"to_date": "2026-01-31",
			},
		)
