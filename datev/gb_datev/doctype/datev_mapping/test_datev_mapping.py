# Copyright (c) 2026, Gaertnerei Berger and contributors
# See license.txt

import json
from pathlib import Path
import unittest


class TestDATEVMapping(unittest.TestCase):
	def test_doctype_uses_generated_name_expression(self):
		doctype_path = Path(__file__).with_name("datev_mapping.json")
		doctype_definition = json.loads(doctype_path.read_text())

		self.assertEqual(
			doctype_definition["autoname"],
			"format:{voucher_type} - {datev_configuration}",
		)
		self.assertEqual(doctype_definition["naming_rule"], "Expression")
