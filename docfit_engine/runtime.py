"""Legacy exports adapt once at the boundary; engine runs use isolated RunContext.

Tk legacy views retain their own compatibility namespace. Engine functions are
rebound to a per-invocation state dictionary, never the bootstrap dictionary.
Explicit contexts never publish state back to a caller's bootstrap namespace.
"""
from importlib import import_module
from threading import RLock
from types import FunctionType
from functools import update_wrapper
from .context import RunContext, current_context

_install_lock = RLock()
_code_globals = {}

def _uses_globals(code):
    cached = _code_globals.get(code)
    if cached is not None:
        return cached
    import dis
    found = any(i.opname in ("LOAD_GLOBAL", "STORE_GLOBAL", "DELETE_GLOBAL") for i in dis.get_instructions(code)) or any(
        _uses_globals(c) for c in code.co_consts if hasattr(c, "co_code"))
    _code_globals[code] = found
    return found


def _plain_bind(function, namespace):
    bound = FunctionType(function.__code__, namespace, function.__name__,
                         function.__defaults__, function.__closure__)
    bound.__kwdefaults__ = function.__kwdefaults__
    bound.__annotations__ = function.__annotations__.copy()
    bound.__dict__.update(function.__dict__)
    bound.__doc__ = function.__doc__
    bound.__qualname__ = function.__name__
    bound.__module__ = namespace.get('__name__', '__main__')
    return bound


class EngineSession:
    def __init__(self, namespace):
        self.namespace = namespace
        self.templates = {}
        self.lock = RLock()

    def new_context(self, *, options=None, profile=None, callbacks=None, state=None, isolate=True, legacy=False, cancellation=None):
        initial = dict(self.namespace)
        if state:
            initial.update(state)
        if isolate:
            for key in ("hwp", "작업_hwp_hwnd"):
                if state is None or key not in state:
                    initial[key] = None
        if legacy and cancellation is None:
            cancellation = self.namespace.get("중단_event")
        context = RunContext(initial, options=options, profile=profile, callbacks=callbacks, isolate=isolate, cancellation=cancellation)
        if legacy:
            context.legacy_source = self.namespace
        return context.install(self.templates, initial)

    def call(self, name, args, kwargs):
        explicit = kwargs.pop("context", None)
        callbacks = kwargs.pop("callbacks", None)
        active = explicit or current_context()
        if active is not None:
            if not active.templates:
                active.install(self.templates, self.namespace)
            if callbacks is not None:
                active.callbacks = callbacks
            if name == "작업_실행" and explicit is not None:
                import inspect
                bound = inspect.signature(self.templates[name][0]).bind_partial(*args, **kwargs)
                options = active.options
                defaults = {"실행모드": options.effective_mode,
                            "표자간조정": options.effective_table_spacing,
                            "자동닫기": options.autoclose, "검수": options.verify_result,
                            "쪽범위": active.state.get("쪽범위_요청")}
                if active.profile:
                    defaults["표준서식_세부"] = active.profile
                for key, value in defaults.items():
                    if key not in bound.arguments:
                        kwargs[key] = value
            return active.invoke(name, *args, **kwargs)
        # Legacy helper exports borrow explicit mutable ports for compatibility.
        # Job entrypoints isolate container state; GUI uses an explicit
        # per-run context and never holds the adapter lock across an execution.
        with self.lock:
            context = self.new_context(callbacks=callbacks, isolate=(name == '작업_실행'), legacy=True)
        try:
            return context.invoke(name, *args, **kwargs)
        finally:
            with self.lock:
                for key, value in context.state.items():
                    if key.startswith("__") or key in self.templates or key in ("gui_queue", "_docfit_engine_session"):
                        continue
                    self.namespace[key] = value


def session_for(namespace):
    session = namespace.get("_docfit_engine_session")
    if not isinstance(session, EngineSession):
        session = EngineSession(namespace)
        namespace["_docfit_engine_session"] = session
    return session


def bind_function(function, namespace):
    if not function.__code__.co_filename.replace("\\", "/").split("/")[-2].startswith("docfit_engine"):
        return _plain_bind(function, namespace)
    session = session_for(namespace)
    if not _uses_globals(function.__code__):
        pure = _plain_bind(function, {"__builtins__": namespace.get("__builtins__", __builtins__)})
        session.templates[function.__name__] = function, pure
        return pure
    name = function.__name__

    def export(*args, **kwargs):
        return session.call(name, args, kwargs)

    facade = _plain_bind(export, namespace)
    update_wrapper(facade, function)
    if name in ("작업_실행", "문서_처리_1회", "_문서_처리_1회", "문서_처리"):
        import inspect
        signature = inspect.signature(function)
        facade.__signature__ = signature.replace(parameters=[
            *signature.parameters.values(),
            inspect.Parameter("context", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("callbacks", inspect.Parameter.KEYWORD_ONLY, default=None),
        ])
    session.templates[name] = function, facade
    return facade


def bind_class(cls, namespace):
    for name, member in list(vars(cls).items()):
        if isinstance(member, FunctionType):
            setattr(cls, name, _plain_bind(member, namespace))
        elif isinstance(member, property):
            setattr(cls, name, property(
                _plain_bind(member.fget, namespace) if member.fget else None,
                _plain_bind(member.fset, namespace) if member.fset else None,
                _plain_bind(member.fdel, namespace) if member.fdel else None,
                member.__doc__))
        elif isinstance(member, (staticmethod, classmethod)):
            setattr(cls, name, type(member)(_plain_bind(member.__func__, namespace)))
    cls.__module__ = namespace.get('__name__', '__main__')
    return cls


def resolve(module, name, namespace):
    with _install_lock:
        return import_module(module)._install(_docfit_namespace=namespace, _docfit_symbol=name)
