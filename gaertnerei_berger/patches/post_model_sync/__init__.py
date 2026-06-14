"""Compatibility shim for the legacy post-model-sync patch package."""

from gaertnerei_berger import _alias_module

_alias_module(__name__, "datev.patches.post_model_sync")
