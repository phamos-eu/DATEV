"""Compatibility package for legacy ``datev.gb_datev`` imports.

Some shared dev data still points standard metadata at the historical
``GB DATEV`` module path. Forward those imports into the current ``datev``
module tree so migrated sites can resolve both paths during rollout.
"""

from importlib import import_module


_target = import_module("datev.datev")

__file__ = _target.__file__
__path__ = list(_target.__path__)

if __spec__ is not None:
	__spec__.submodule_search_locations = list(__path__)
