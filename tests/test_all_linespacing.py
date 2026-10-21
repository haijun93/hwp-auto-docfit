import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from docfit_app.application_service import ApplicationService
from docfit_app.configuration_service import fields
from docfit_app.settings_schema import DEFAULTS, VARIABLE_BINDINGS


class AllLinespacingTests(unittest.TestCase):
    def test_default_and_variable_binding(self):
        self.assertIs(DEFAULTS['all_linespacing'], True)
        self.assertEqual(VARIABLE_BINDINGS['all_linespacing'], 'all_linespacing_var')

    def test_service_exposes_and_persists_card_option(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            service = ApplicationService(path)
            self.assertIs(service.state()['card_options']['all_linespacing'], True)
            for enabled in (False, True):
                state = service.dispatch('set_card_option', ['all_linespacing', enabled])
                self.assertIs(state['card_options']['all_linespacing'], enabled)
                reloaded = ApplicationService(path)
                self.assertIs(reloaded.state()['card_options']['all_linespacing'], enabled)

    def test_configuration_label(self):
        field = next(item for item in fields() if item['key'] == 'all_linespacing')
        self.assertEqual(field['label'], '한 번에 적용: 줄 간격 적용')
