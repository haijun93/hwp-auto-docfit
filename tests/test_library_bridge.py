import unittest

from docfit_app.library_bridge import LibraryBridge


class FakeProcess:
    def __init__(self):
        self.args = None

    def Popen(self, args, **kwargs):
        self.args = (args, kwargs)


class LibraryBridgeTests(unittest.TestCase):
    def test_search_forwards_unicode_query_box_and_limit(self):
        process = FakeProcess()
        bridge = LibraryBridge(exe="klib.exe", process=process, pipe_factory=lambda: "fake")
        expected = [{"path": "C:/자료/문서.hwpx", "name": "문서.hwpx", "snippet": "행정복지센터"}]
        sent = {}

        def request(cmd, **payload):
            sent.update(cmd=cmd, **payload)
            return {"ok": True, "results": expected}

        bridge.request = request
        self.assertEqual(bridge.library_search("행정복지센터", box_id=4, limit=7), expected)
        self.assertEqual(sent, {"cmd": "search", "query": "행정복지센터", "box_id": 4, "limit": 7})

    def test_invalid_search_options_are_rejected(self):
        bridge = LibraryBridge(pipe_factory=lambda: "fake")
        with self.assertRaises(ValueError):
            bridge.library_search(" ")
        with self.assertRaises(ValueError):
            bridge.library_search("한글", limit=0)
        with self.assertRaises(ValueError):
            bridge.library_search("한글", box_id=True)


if __name__ == "__main__":
    unittest.main()
