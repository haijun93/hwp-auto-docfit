"""Document identity and isolated, in-memory working model (no COM dependency)."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from threading import RLock
from uuid import uuid4


class RevisionConflict(RuntimeError):
    """The caller edited an obsolete document revision."""


class DocumentSession:
    """One working copy and model. File serialization belongs to an adapter.

    Public model reads are defensive copies. Only CommandBus commits edits;
    commands never receive the session or a writable original document path.
    """

    def __init__(self, document_id, original_hash, working_copy_path, state=None):
        if not document_id or not original_hash:
            raise ValueError("document_id and original_hash are required")
        if state is not None and not isinstance(state, dict):
            raise TypeError("state must be a dictionary")
        self._document_id = document_id
        self._original_hash = original_hash
        self._working_copy_path = Path(working_copy_path).resolve()
        self._revision = 0
        self._state = deepcopy(state if state is not None else {})
        self._saved_state = deepcopy(self._state)
        self._lock = RLock()
        self._executing = False

    @classmethod
    def open(cls, original_path, working_copy_path, state=None):
        """Create a new copy exclusively; never overwrite an existing file."""
        original = Path(original_path).resolve()
        working = Path(working_copy_path).resolve()
        if original == working:
            raise ValueError("working copy must differ from original")
        content = original.read_bytes()
        with working.open("xb") as stream:
            stream.write(content)
        return cls(str(uuid4()), sha256(content).hexdigest(), working, state)

    document_id = property(lambda self: self._document_id)
    original_hash = property(lambda self: self._original_hash)
    working_copy_path = property(lambda self: self._working_copy_path)

    @property
    def revision(self):
        with self._lock:
            return self._revision

    @property
    def state(self):
        with self._lock:
            return deepcopy(self._state)

    def snapshot(self):
        """Return (revision, model) under one lock for save/preview adapters."""
        with self._lock:
            return self._revision, deepcopy(self._state)

    @property
    def dirty(self):
        with self._lock:
            return self._state != self._saved_state

    def mark_saved(self, *, expected_revision):
        """Adapter calls only after successfully saving this exact revision."""
        with self._lock:
            self._check_revision(expected_revision)
            if self._executing:
                raise RuntimeError("cannot save during a command")
            self._saved_state = deepcopy(self._state)

    def _check_revision(self, expected_revision):
        if expected_revision != self._revision:
            raise RevisionConflict(
                f"expected revision {expected_revision}, actual {self._revision}"
            )
