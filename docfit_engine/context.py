"""Per-run engine state and ports. No bootstrap or Tk imports."""
from contextvars import ContextVar
from contextlib import contextmanager
from types import FunctionType

from defusedxml.ElementTree import fromstring as _safe_xml
_XML_TYPE = type(_safe_xml("<context/>"))

_active = ContextVar("docfit_run_context", default=None)


def current_context():
    return _active.get()


def _clone(value, memo):
    if isinstance(value, _XML_TYPE):
        import copy
        return copy.deepcopy(value, memo)
    if type(value) is bytearray:
        return bytearray(value)
    if type(value) not in (dict, list, set, tuple):
        return value  # COM handles, locks, modules and callbacks are explicit ports.
    identity = id(value)
    if identity in memo:
        return memo[identity]
    if type(value) is dict:
        result = {}
        memo[identity] = result
        result.update((key, _clone(item, memo)) for key, item in value.items())
    elif type(value) is list:
        result = []
        memo[identity] = result
        result.extend(_clone(item, memo) for item in value)
    elif type(value) is set:
        result = set(value)
        memo[identity] = result
    else:
        result = tuple(_clone(item, memo) for item in value)
        memo[identity] = result
    return result


class EventPort:
    def __init__(self, context):
        self.context = context

    def put(self, event):
        self.context.emit(event)


class RunContext:
    """Owns options, profile, COM/session state, bound engine and reporting ports."""

    def __init__(self, state=None, *, options=None, profile=None, callbacks=None, isolate=True, cancellation=None):
        from docfit_core.app_state import RunOptions
        from dataclasses import replace
        self.options = replace(options) if options is not None else RunOptions()
        self.profile = _clone(profile or {}, {})
        memo = {}
        self.state = {key: (value if key.startswith("__") or not isolate else _clone(value, memo))
                      for key, value in (state or {}).items()}
        import threading
        self.cancellation = cancellation if cancellation is not None else threading.Event()
        self.state["중단_event"] = self.cancellation
        if isolate:
            self.state.setdefault("hwp", None)
            self.state.setdefault("작업_hwp_hwnd", None)
        self._memo = memo
        self.isolate = isolate
        self.functions = {}
        self.templates = {}
        self.legacy_source = None
        self.synced = {}  # values the legacy adapter pushed into legacy_source
        if options is not None:
            self.state["작업_모드"] = options.effective_mode
            self.state["표_자간조정_사용"] = options.effective_table_spacing
            # '페이지 맞춤' 카드(자간 끔·쪽 맞춤만): 결과 이름을 (페이지맞춤)으로.
            self.state["쪽맞춤만"] = (options.effective_mode == "spacing" and not options.spacing_enabled
                                  and not options.spacing_exclude_pagefit)
            value = options.page_range
            if value:
                parts = str(value).split("-", 1)
                start = int(parts[0])
                end = int(parts[-1]) if parts[-1] else None
                if start < 1 or (end is not None and end < start):
                    raise ValueError("잘못된 쪽 범위")
                self.state["쪽범위_요청"] = (start, end)
            else:
                self.state["쪽범위_요청"] = None
            self.state["자동닫기_설정"] = options.autoclose
            self.state["검수_사용"] = options.verify_result
        self._sink = getattr(self.state.get("gui_queue"), "put", lambda event: None)
        from .pipeline import PipelineCallbacks
        self.callbacks = callbacks or PipelineCallbacks(
            log=self._default_log,
            status=lambda text: self._sink(("status", str(text))),
            progress=lambda text: self._sink(("step", text)),
        )
        self.state["gui_queue"] = EventPort(self)

    def _default_log(self, message):
        text = str(message)
        if self.state.get("_콘솔_출력_가능"):
            try:
                print(text)
            except Exception:
                pass
        if self.state.get("로그파일_사용") and self.state.get("로그_파일_경로"):
            try:
                import datetime
                with self.state["로그_파일_잠금"]:
                    with open(self.state["로그_파일_경로"], "a", encoding="utf-8") as stream:
                        stream.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S.%f} {text}\n")
            except OSError:
                pass
        self._sink(("log", text))

    def emit(self, event):
        if self.callbacks.event is not None:
            self.callbacks.event(event)
        else:
            self._sink(event)

    @contextmanager
    def activate(self):
        token = _active.set(self)
        try:
            yield self
        finally:
            _active.reset(token)

    def install(self, templates, source):
        for key, value in source.items():
            if key not in self.state:
                self.state[key] = _clone(value, self._memo) if self.isolate and not key.startswith("__") else value
        self.templates = templates
        for name, (_, facade) in templates.items():
            self.state.setdefault(name, source.get(name, facade))
            supplied = self.state[name]
            if self.legacy_source is not None and supplied is not facade and callable(supplied):
                self.state[name] = self._legacy_callback(supplied)
        return self

    def _legacy_callback(self, callback):
        # Test/legacy embedding overrides may intentionally read/write their
        # original namespace. Adapt that port only; isolated contexts never do.
        def call(*args, **kwargs):
            source = self.legacy_source
            for key, value in self.state.items():
                if key not in self.templates and not key.startswith("__") and key not in ("gui_queue", "_docfit_engine_session"):
                    source[key] = value
                    self.synced[key] = value
            before = dict(source)
            try:
                return callback(*args, **kwargs)
            finally:
                for key, value in source.items():
                    if key not in self.templates and (key not in before or before[key] is not value):
                        self.state[key] = value
        return call

    def function(self, name):
        if name not in self.functions:
            template, facade = self.templates[name]
            bound = FunctionType(template.__code__, self.state, template.__name__,
                                 (_clone(template.__defaults__, self._memo) if self.isolate else template.__defaults__), template.__closure__)
            bound.__kwdefaults__ = _clone(template.__kwdefaults__, self._memo) if self.isolate else template.__kwdefaults__
            bound.__annotations__ = template.__annotations__.copy()
            self.functions[name] = bound
            if self.state.get(name) is facade:
                self.state[name] = bound
        return self.functions[name]

    def invoke(self, name, *args, **kwargs):
        with self.activate():
            return self.function(name)(*args, **kwargs)
