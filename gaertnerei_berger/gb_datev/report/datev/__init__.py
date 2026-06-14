"""Compatibility shim for the legacy DATEV report package."""

from gaertnerei_berger import _alias_module

_alias_module(__name__, "datev.gb_datev.report.datev")
