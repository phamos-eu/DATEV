"""Compatibility shim for the legacy DATEV Settings package."""

from gaertnerei_berger import _alias_module

_alias_module(__name__, "datev.gb_datev.doctype.datev_settings")
