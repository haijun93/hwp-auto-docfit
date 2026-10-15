"""Temporary folders for tests that are removed when the test finishes."""
import shutil
import tempfile


def tracked_tempdir(test, prefix):
    """Create a temp folder and register its removal on the given TestCase."""
    folder = tempfile.mkdtemp(prefix=prefix)
    test.addCleanup(shutil.rmtree, folder, ignore_errors=True)
    return folder
