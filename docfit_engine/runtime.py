"""Compatibility binding for the flat public API and its mutable COM session.

Each installation binds function globals to the caller's session, never a copy.
This preserves runpy isolation, late monkeypatches and mutable COM handles while
source ownership moves out of the bootstrap. UI objects are not exported here.
Only trusted package definitions are installed; no user code is evaluated.
"""
from importlib import import_module
from threading import RLock
from types import FunctionType

_install_lock = RLock()


def bind_function(function, namespace):
    bound = FunctionType(function.__code__, namespace, function.__name__,
                         function.__defaults__, function.__closure__)
    bound.__kwdefaults__ = function.__kwdefaults__
    bound.__annotations__ = function.__annotations__.copy()
    bound.__dict__.update(function.__dict__)
    bound.__doc__ = function.__doc__
    bound.__qualname__ = function.__name__
    bound.__module__ = namespace.get('__name__', '__main__')
    return bound


def bind_class(cls, namespace):
    for name, member in list(vars(cls).items()):
        if isinstance(member, FunctionType):
            setattr(cls, name, bind_function(member, namespace))
        elif isinstance(member, property):
            setattr(cls, name, property(
                bind_function(member.fget, namespace) if member.fget else None,
                bind_function(member.fset, namespace) if member.fset else None,
                bind_function(member.fdel, namespace) if member.fdel else None,
                member.__doc__))
        elif isinstance(member, (staticmethod, classmethod)):
            setattr(cls, name, type(member)(bind_function(member.__func__, namespace)))
    cls.__module__ = namespace.get('__name__', '__main__')
    return cls


def resolve(module, name, namespace):
    with _install_lock:
        return import_module(module)._install(_docfit_namespace=namespace, _docfit_symbol=name)
