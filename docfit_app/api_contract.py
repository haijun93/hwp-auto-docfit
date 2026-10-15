"""Versioned JSON responses for the new service API only."""

API_VERSION = 1


class ServiceError(Exception):
    def __init__(self, code, message, recoverable=True):
        super().__init__(message)
        self.code = code
        self.recoverable = recoverable


def response(action):
    try:
        return {"api_version": API_VERSION, "ok": True, "data": action(), "error": None}
    except ServiceError as exc:
        return {"api_version": API_VERSION, "ok": False, "data": None,
                "error": {"code": exc.code, "message": str(exc), "recoverable": exc.recoverable}}
