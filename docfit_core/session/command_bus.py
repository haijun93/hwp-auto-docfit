"""Atomic model transactions and document-scoped snapshot history."""
from copy import deepcopy
from dataclasses import dataclass
from typing import MutableMapping, Protocol

from .document_session import DocumentSession, RevisionConflict


class Command(Protocol):
    def apply(self, draft: MutableMapping) -> None:
        """Mutate only draft; external file/COM side effects are forbidden."""


@dataclass(frozen=True)
class _Entry:
    before: dict
    after: dict


class HistoryService:
    """Read-only history status; mutations are owned by its CommandBus."""

    def __init__(self):
        self._undo = []
        self._redo = []
        self._owner = None

    can_undo = property(lambda self: bool(self._undo))
    can_redo = property(lambda self: bool(self._redo))
    undo_count = property(lambda self: len(self._undo))
    redo_count = property(lambda self: len(self._redo))


class CommandBus:
    def __init__(self, session: DocumentSession, history=None):
        self.session = session
        self.history = history if history is not None else HistoryService()
        if self.history._owner is not None:
            raise ValueError("history already belongs to a command bus")
        self.history._owner = self
        self._head = session.revision

    def _check(self, expected_revision):
        self.session._check_revision(expected_revision)
        if self.session._executing:
            raise RuntimeError("nested commands are forbidden")
        if self._head != self.session.revision:
            raise RevisionConflict("history diverged; create a new command bus")

    def _commit(self, state):
        self.session._state = state
        self.session._revision += 1
        self._head = self.session._revision
        return self._head

    def execute(self, command: Command, *, expected_revision):
        return self.execute_batch([command], expected_revision=expected_revision)

    def execute_batch(self, commands, *, expected_revision):
        """All commands succeed as one history entry, or nothing changes."""
        with self.session._lock:
            self._check(expected_revision)
            self.session._executing = True
            try:
                commands = tuple(commands)
                if not commands:
                    raise ValueError("empty transaction")
                before = deepcopy(self.session._state)
                draft = deepcopy(before)
                for command in commands:
                    command.apply(draft)
                # Detach any references retained by commands before publication.
                after = deepcopy(draft)
                published = deepcopy(after)
                entry = _Entry(before, after)
                self.history._undo.append(entry)
                self.history._redo.clear()
                return self._commit(published)
            finally:
                self.session._executing = False

    def _move(self, source, destination, field, expected_revision):
        with self.session._lock:
            self._check(expected_revision)
            if not source:
                raise IndexError("history is empty")
            entry = source[-1]
            state = deepcopy(getattr(entry, field))
            destination.append(entry)
            source.pop()
            return self._commit(state)

    def undo(self, *, expected_revision):
        return self._move(self.history._undo, self.history._redo,
                          "before", expected_revision)

    def redo(self, *, expected_revision):
        return self._move(self.history._redo, self.history._undo,
                          "after", expected_revision)
