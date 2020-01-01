"""Convenience functions for doing asserts with helpful names and helpful messages."""

# NOTE TO IMPLEMENTORS:
# This module depends on the contracts described in our sibling module ``check``.
# In the spirit of DRY, please see that module for details.


from inspect import getmodule as _getmodule
from inspect import getmembers as _getmembers
from inspect import isfunction as _isfunction

from wrapt import decorator as _decorator

from . import check as _check

# Used internally, but there is no reason to prevent it from being used externally.
@_decorator
def assert_if_truthy(wrapped, instance, args, kwargs):
    """Assert if the decorated function returns a truthy value (error indicator)."""
    result = wrapped(*args, **kwargs)
    assert not result, result


def _make_asserter(member):
    """
    Make fun part of member an asserting function _and_ take ownership of the wrapper.

    wrapt preserves a little _too_ much and we want the wrapped function
    to have a more accurate doc string and a module attribute that shows it belongs
    to us instead of ``check``, which could be confusing.
    """
    name, fun = member
    new_fun = assert_if_truthy(fun)
    new_fun.__doc__ = new_fun.__doc__.replace("Check", "Assert")
    new_fun.__module__ = __name__
    return (name, new_fun)


def _is_exported_name(name):
    """Is ``name`` something that check wants exported."""
    # If ``check`` ever switches to using the ``__all__`` mechanism, update this code:
    return not name.startswith("_")


def _should_be_wrapped(member):
    name, obj = member
    return _is_exported_name(name) and _isfunction(obj) and _getmodule(obj) == _check


globals().update(map(_make_asserter, filter(_should_be_wrapped, _getmembers(_check))))
