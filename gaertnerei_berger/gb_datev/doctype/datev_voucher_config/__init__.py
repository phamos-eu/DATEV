"""Compatibility shim for the legacy DATEV Voucher Config package."""

from gaertnerei_berger import _alias_module

_alias_module(__name__, "datev.gb_datev.doctype.datev_voucher_config")
