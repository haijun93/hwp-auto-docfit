"""Compatibility facade for the pure core settings migration."""
from .settings_schema import DEFAULTS
from docfit_core.config_store import migrate_settings


def migrate(settings):
    return migrate_settings(settings, DEFAULTS)
