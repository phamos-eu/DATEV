import sys
from importlib import import_module

from datev import __version__


def _alias_package(alias: str, target: str) -> None:
	module = import_module(target)
	sys.modules[f"{__name__}.{alias}"] = module
	globals()[alias] = module


for alias_name, target_name in (
	("config", "datev.config"),
	("gb_datev", "datev.gb_datev"),
	("patches", "datev.patches"),
	("templates", "datev.templates"),
	("utils", "datev.utils"),
):
	_alias_package(alias_name, target_name)
