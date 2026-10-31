import tempfile
import unittest
from pathlib import Path

from docfit_app.application_service import ApplicationService


class SidebarSettingTest(unittest.TestCase):
    def test_collapsed_state_survives_restart_and_defaults_to_none(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            service = ApplicationService(path)
            try:
                self.assertIsNone(service.dispatch("get_state", [])["sidebar_collapsed"])
                service.dispatch("set_sidebar_collapsed", [True])
            finally:
                service.close() if hasattr(service, "close") else None
            reloaded = ApplicationService(path)
            try:
                self.assertIs(reloaded.dispatch("get_state", [])["sidebar_collapsed"], True)
                reloaded.dispatch("get_settings", [])
                self.assertIs(reloaded.dispatch("get_state", [])["sidebar_collapsed"], True)
            finally:
                reloaded.close() if hasattr(reloaded, "close") else None


if __name__ == "__main__":
    unittest.main()
