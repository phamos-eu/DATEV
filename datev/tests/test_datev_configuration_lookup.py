import unittest
from unittest.mock import patch

import frappe

from datev.datev.report.datev.datev import (
	download_datev_csv,
	get_buchungsstapel_mappings,
	get_datev_configuration,
	validate,
)


class TestDatevConfigurationLookup(unittest.TestCase):
	def test_get_datev_configuration_looks_up_by_company_field(self):
		configuration = frappe._dict(
			{
				"name": "_Test GmbH",
				"account_number_length": 4,
				"temporary_against_account_number": "9999",
				"opening_against_account_number": "9000",
			}
		)

		with patch(
			"datev.datev.report.datev.datev.frappe.get_value",
			return_value=configuration,
		) as get_value_mock:
			result = get_datev_configuration("_Test GmbH")

		get_value_mock.assert_called_once_with(
			"DATEV Configuration",
			{"company": "_Test GmbH"},
			[
				"name",
				"account_number_length",
				"temporary_against_account_number",
				"opening_against_account_number",
			],
			as_dict=1,
		)
		self.assertEqual(result.name, "_Test GmbH")

	def test_validate_accepts_company_matched_configuration(self):
		filters = {
			"company": "_Test GmbH",
			"from_date": "2026-06-10",
			"to_date": "2026-06-10",
		}

		with (
			patch(
				"datev.datev.report.datev.datev.validate_fiscal_year"
			) as validate_fiscal_year_mock,
			patch(
				"datev.datev.report.datev.datev.get_datev_configuration",
				return_value=frappe._dict({"name": "_Test GmbH"}),
			),
		):
			self.assertTrue(validate(filters))

		validate_fiscal_year_mock.assert_called_once_with("2026-06-10", "2026-06-10", "_Test GmbH")

	def test_download_uses_company_lookup_configuration(self):
		filters = {
			"company": "_Test GmbH",
			"from_date": "2026-06-10",
			"to_date": "2026-06-10",
		}
		datev_configuration = frappe._dict(
			{
				"name": "_Test GmbH",
				"account_number_length": 6,
				"temporary_against_account_number": "123456",
				"opening_against_account_number": "654321",
			}
		)

		with (
			patch("datev.datev.report.datev.datev.frappe.only_for"),
			patch("datev.datev.report.datev.datev.validate", return_value=True),
			patch(
				"datev.datev.report.datev.datev.get_fiscal_year",
				return_value=("FY-2026", "2026-01-01", "2026-12-31"),
			),
			patch(
				"datev.datev.report.datev.datev.frappe.get_value",
				return_value="SKR04 mit Kontonummern",
			),
			patch(
				"datev.datev.report.datev.datev.get_datev_configuration",
				return_value=datev_configuration,
			) as get_datev_configuration_mock,
			patch(
				"datev.datev.report.datev.datev.get_transactions",
				return_value=[],
			) as get_transactions_mock,
			patch(
				"datev.datev.report.datev.datev.group_sales_invoice_buchungsstapel",
				side_effect=lambda transactions, _: transactions,
			),
			patch(
				"datev.datev.report.datev.datev.group_payment_entry_buchungsstapel",
				side_effect=lambda transactions, _: transactions,
			),
			patch(
				"datev.datev.report.datev.datev.apply_buchungsstapel_mapping",
				side_effect=lambda transactions, _: transactions,
			),
			patch("datev.datev.report.datev.datev.get_account_names", return_value=[]),
			patch("datev.datev.report.datev.datev.get_customers", return_value=[]),
			patch("datev.datev.report.datev.datev.get_suppliers", return_value=[]),
			patch("datev.datev.report.datev.datev.get_datev_csv", return_value="csv"),
			patch("datev.datev.report.datev.datev.zip_and_download"),
		):
			download_datev_csv.__wrapped__(filters)

		get_datev_configuration_mock.assert_called_once_with("_Test GmbH")
		self.assertEqual(get_transactions_mock.call_args.args[0]["account_number_length"], 6)
		self.assertEqual(get_transactions_mock.call_args.args[0]["against_account"], "123456")
		self.assertEqual(get_transactions_mock.call_args.args[0]["opening_account"], "654321")
		self.assertEqual(get_transactions_mock.call_args.args[0]["skr"], "04")

	def test_download_throws_controlled_error_when_configuration_is_missing(self):
		filters = {
			"company": "_Test GmbH",
			"from_date": "2026-06-10",
			"to_date": "2026-06-10",
		}

		with (
			patch("datev.datev.report.datev.datev.frappe.only_for"),
			patch("datev.datev.report.datev.datev.validate", return_value=False),
			patch(
				"datev.datev.report.datev.datev.get_missing_datev_configuration_message",
				return_value="Please create DATEV Configuration for Company _Test GmbH",
			),
			patch(
				"datev.datev.report.datev.datev.frappe.throw",
				side_effect=RuntimeError("DATEV Configuration missing"),
			) as throw_mock,
			patch("datev.datev.report.datev.datev.get_fiscal_year") as get_fiscal_year_mock,
		):
			with self.assertRaisesRegex(RuntimeError, "DATEV Configuration missing"):
				download_datev_csv.__wrapped__(filters)

		throw_mock.assert_called_once_with("Please create DATEV Configuration for Company _Test GmbH")
		get_fiscal_year_mock.assert_not_called()

	def test_get_buchungsstapel_mappings_filters_by_configuration(self):
		parent_rows = [frappe._dict({"name": "Sales Invoice - _Test GmbH", "voucher_type": "Sales Invoice"})]
		child_rows = [
			frappe._dict(
				{
					"parent": "Sales Invoice - _Test GmbH",
					"map_to_field": "due_date",
					"map_to_column": "Fälligkeit",
				}
			)
		]

		with (
			patch(
				"datev.datev.report.datev.datev.get_datev_configuration",
				return_value=frappe._dict({"name": "_Test GmbH"}),
			),
			patch(
				"datev.datev.report.datev.datev.frappe.get_all",
				side_effect=[parent_rows, child_rows],
			) as get_all_mock,
		):
			result = get_buchungsstapel_mappings({"Sales Invoice"}, "_Test GmbH")

		self.assertEqual(result["Sales Invoice"][0].map_to_field, "due_date")
		self.assertEqual(
			get_all_mock.call_args_list[0].kwargs["filters"],
			{
				"datev_configuration": "_Test GmbH",
				"voucher_type": ["in", ["Sales Invoice"]],
			},
		)
