"""Compatibility shim for the legacy ``gaertnerei_berger.patches`` package."""

from gaertnerei_berger import _alias_module

_alias_module(__name__, "datev.patches")
