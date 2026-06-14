"""Compatibility shim for the legacy ``gaertnerei_berger.templates`` package."""

from gaertnerei_berger import _alias_module

_alias_module(__name__, "datev.templates")
