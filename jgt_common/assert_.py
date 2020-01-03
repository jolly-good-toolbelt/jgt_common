"""Convenience functions for doing asserts with helpful names and helpful messages."""

# NOTE TO IMPLEMENTORS:
# This module depends on the contracts described in our sibling module ``check``.
# In the spirit of DRY, please see that module for details.


from functools import wraps as _wraps
from inspect import getmodule as _getmodule
from inspect import getmembers as _getmembers
from inspect import isfunction as _isfunction

from . import check as _check


# Used internally, but there is no reason to prevent it from being used externally.
def assert_if_truthy(fun):
    """(Decorator) Assert if fun returns a truthy value (error indicator)."""

    # NOTE: Not using ``wrapt`` because it forwards attributes
    #       from the wrapping function to the wrapped function,
    #       which will break the code in _make_asserter.
    @_wraps(fun)
    def wrapper(*args, **kwargs):
        result = fun(*args, **kwargs)
        assert not result, result

    return wrapper


def _make_asserter(member):
    """
    Make fun part of member an asserting function _and_ take ownership of the wrapper.

    The wrapped function should have a correct doc string,
    and a module attribute that shows it belongs
    to us instead of ``check``, which could be confusing.
    """
    name, fun = member
    new_fun = assert_if_truthy(fun)
    if new_fun.__doc__:
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
