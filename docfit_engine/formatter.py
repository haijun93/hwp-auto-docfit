"""Compatibility exports for formatter definitions split by feature.

Raw exports retain this module's globals for existing patch targets. Runtime
exports are still rebound by bind_function into each invocation's RunContext.
"""
from docfit_engine.runtime import bind_function, bind_class, _plain_bind
from . import formatter_utils
from . import formatter_analysis
from . import formatter_titles
from . import formatter_tables
from . import formatter_apply
from . import formatter_indent
from . import formatter_unify
from . import formatter_text

_SPLIT_INSTALLERS = {}
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_utils.SYMBOLS, formatter_utils._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_analysis.SYMBOLS, formatter_analysis._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_titles.SYMBOLS, formatter_titles._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_tables.SYMBOLS, formatter_tables._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_apply.SYMBOLS, formatter_apply._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_indent.SYMBOLS, formatter_indent._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_unify.SYMBOLS, formatter_unify._install))
_SPLIT_INSTALLERS.update(dict.fromkeys(formatter_text.SYMBOLS, formatter_text._install))


def _export_split_function(function, namespace):
    # A raw re-export must look up dependencies through formatter.X, so patches
    # of that path continue to affect calls across feature module boundaries.
    exported = _plain_bind(function, globals())
    exported.__qualname__ = function.__qualname__
    globals()[function.__name__] = exported
    return exported


def _bind_split_function(function, namespace):
    return bind_function(_export_split_function(function, namespace), namespace)


def __getattr__(name):
    installer = _SPLIT_INSTALLERS.get(name)
    if installer is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return installer(_docfit_namespace=globals(), _docfit_symbol=name,
                     bind_function=_export_split_function)


def _install(*, _docfit_namespace, _docfit_symbol):
    installer = _SPLIT_INSTALLERS.get(_docfit_symbol)
    if installer is not None:
        return installer(_docfit_namespace=_docfit_namespace, _docfit_symbol=_docfit_symbol,
                         bind_function=_bind_split_function)
    raise KeyError(_docfit_symbol)
