import unittest
from unittest.mock import Mock, patch

from datev.tests._module_stubs import import_with_framework_stubs

datev_module = import_with_framework_stubs("datev.gb_datev.report.datev.datev")
get_buchungsstapel_mappings = datev_module.get_buchungsstapel_mappings


class TestDatevMappingLookupCompatibility(unittest.TestCase):
	def test_omits_configuration_filter_when_field_is_missing(self):
		meta = Mock()
		meta.has_field.return_value = False

		with patch(
			"datev.gb_datev.report.datev.datev.frappe.get_meta", return_value=meta
		), patch(
			"datev.gb_datev.report.datev.datev.frappe.get_all", return_value=[]
		) as get_all_mock:
			get_buchungsstapel_mappings({"Sales Invoice"}, "DATEV Dummy GmbH")

		self.assertEqual(
			get_all_mock.call_args.kwargs["filters"],
			{"voucher_type": ["in", ["Sales Invoice"]]},
		)

	def test_keeps_configuration_filter_when_field_exists(self):
		meta = Mock()
		meta.has_field.return_value = True

		with patch(
			"datev.gb_datev.report.datev.datev.frappe.get_meta", return_value=meta
		), patch(
			"datev.gb_datev.report.datev.datev.frappe.get_all", return_value=[]
		) as get_all_mock:
			get_buchungsstapel_mappings({"Sales Invoice"}, "DATEV Dummy GmbH")

		self.assertEqual(
			get_all_mock.call_args.kwargs["filters"],
			{
				"voucher_type": ["in", ["Sales Invoice"]],
				"datev_configuration": "DATEV Dummy GmbH",
			},
		)
