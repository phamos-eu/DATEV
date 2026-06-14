import importlib
import sys
from datetime import date
from types import ModuleType, SimpleNamespace


def _dict(values=None, **kwargs):
	data = {}
	if values:
		data.update(values)
	data.update(kwargs)
	return SimpleNamespace(**data)


def _identity_decorator(*args, **kwargs):
	def decorate(function):
		function.__wrapped__ = function
		return function

	return decorate


def install_framework_stubs():
	frappe_module = sys.modules.get("frappe")
	if frappe_module is None:
		frappe_module = ModuleType("frappe")
		frappe_module.__dict__.update(
			{
				"_": lambda value: value,
				"_dict": _dict,
				"DoesNotExistError": type("DoesNotExistError", (Exception,), {}),
				"db": SimpleNamespace(
					get_value=lambda *args, **kwargs: None,
					sql=lambda *args, **kwargs: [],
					exists=lambda *args, **kwargs: False,
					commit=lambda: None,
				),
				"delete_doc": lambda *args, **kwargs: None,
				"get_all": lambda *args, **kwargs: [],
				"get_doc": lambda *args, **kwargs: _dict(name=None),
				"get_meta": lambda *args, **kwargs: SimpleNamespace(has_field=lambda fieldname: False),
				"get_value": lambda *args, **kwargs: None,
				"local": SimpleNamespace(flags=SimpleNamespace()),
				"log_error": lambda *args, **kwargs: None,
				"only_for": lambda *args, **kwargs: None,
				"response": {},
				"session": SimpleNamespace(user="test@example.com"),
				"throw": lambda message, *args, **kwargs: (_ for _ in ()).throw(RuntimeError(message)),
				"utils": SimpleNamespace(
					formatdate=lambda value, _format=None: value,
					datetime=SimpleNamespace(date=date),
				),
				"whitelist": _identity_decorator,
			}
		)
		sys.modules["frappe"] = frappe_module

	erpnext_module = sys.modules.get("erpnext")
	if erpnext_module is None:
		erpnext_module = ModuleType("erpnext")
		sys.modules["erpnext"] = erpnext_module

	accounts_module = sys.modules.get("erpnext.accounts")
	if accounts_module is None:
		accounts_module = ModuleType("erpnext.accounts")
		sys.modules["erpnext.accounts"] = accounts_module

	utils_module = sys.modules.get("erpnext.accounts.utils")
	if utils_module is None:
		utils_module = ModuleType("erpnext.accounts.utils")
		utils_module.get_fiscal_year = lambda *args, **kwargs: ("FY-2026", "2026-01-01", "2026-12-31")
		sys.modules["erpnext.accounts.utils"] = utils_module

	doctype_module = sys.modules.get("erpnext.accounts.doctype")
	if doctype_module is None:
		doctype_module = ModuleType("erpnext.accounts.doctype")
		sys.modules["erpnext.accounts.doctype"] = doctype_module

	payment_entry_package = sys.modules.get("erpnext.accounts.doctype.payment_entry")
	if payment_entry_package is None:
		payment_entry_package = ModuleType("erpnext.accounts.doctype.payment_entry")
		sys.modules["erpnext.accounts.doctype.payment_entry"] = payment_entry_package

	payment_entry_module = sys.modules.get("erpnext.accounts.doctype.payment_entry.payment_entry")
	if payment_entry_module is None:
		payment_entry_module = ModuleType("erpnext.accounts.doctype.payment_entry.payment_entry")
		payment_entry_module.get_payment_entry = lambda *args, **kwargs: _dict(name="PAY-TEST")
		sys.modules["erpnext.accounts.doctype.payment_entry.payment_entry"] = payment_entry_module

	pandas_module = sys.modules.get("pandas")
	if pandas_module is None:
		pandas_module = ModuleType("pandas")
		pandas_module.DataFrame = SimpleNamespace
		pandas_module.concat = lambda frames, ignore_index=False: SimpleNamespace(
			to_csv=lambda **kwargs: "",
			sort_values=lambda **sort_kwargs: SimpleNamespace(to_csv=lambda **csv_kwargs: ""),
		)
		pandas_module.to_datetime = lambda values: values
		sys.modules["pandas"] = pandas_module


def import_with_framework_stubs(module_name):
	install_framework_stubs()
	return importlib.import_module(module_name)
