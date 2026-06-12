"""Compatibility package for legacy report imports under ``datev.gb_datev``."""

from importlib import import_module


_target = import_module("datev.datev.report")

__file__ = _target.__file__
__path__ = list(_target.__path__)

if __spec__ is not None:
	__spec__.submodule_search_locations = list(__path__)
