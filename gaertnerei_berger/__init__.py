import sys
from importlib import import_module

from datev import __version__


def _alias_module(module_name: str, target: str):
	module = import_module(target)
	sys.modules[module_name] = module
	return module


def _alias_package(alias: str, target: str) -> None:
	module = _alias_module(f"{__name__}.{alias}", target)
	globals()[alias] = module


for alias_name, target_name in (
	("config", "datev.config"),
	("gb_datev", "datev.gb_datev"),
	("patches", "datev.patches"),
	("templates", "datev.templates"),
	("utils", "datev.utils"),
):
	_alias_package(alias_name, target_name)
