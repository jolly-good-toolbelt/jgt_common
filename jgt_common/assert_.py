"""Convenience functions for doing asserts with helpful names and helpful messages."""

# NOTE TO IMPLEMENTORS:
# This module depends on the contracts described in our sibling module ``check``.
# In the spirit of DRY, please see that module for details.


from inspect import isfunction as _isfunction

import wrapt as _wrapt

from . import check as _check

_check_module_name = _check.__name__

_glbls = globals()


# Used internally, but there is no reason to prevent it from being used externally.
@_wrapt.decorator
def assert_if_truthy(wrapped, instance, args, kwargs):
    """Assert if the decorated function returns a truthy value (error indicator)."""
    result = wrapped(*args, **kwargs)
    assert not result, result


def _pretty_assert_for(fun):
    """
    Make fun an asserting function _and_ take ownership of the wrapper.

    wrapt preserves a little _too_ much and we want the wrapped function
    to have a more accurate doc string and a module attribute that shows it belongs
    to us instead of ``check``, which could be confusing.
    """
    new_fun = assert_if_truthy(fun)
    new_fun.__doc__ = new_fun.__doc__.replace("Check", "Assert")
    new_fun.__module__ = __name__
    return new_fun


for _thing_name in dir(_check):
    # If the check module ever defines __all__ we should use that here,
    # for now use the standard python convention...
    if _thing_name.startswith("_"):
        continue

    _thing = getattr(_check, _thing_name)

    # The check module should be clean and only import things with
    # the underscore prefix, but we're being extra careful here:
    if getattr(_thing, "__module__", None) != _check_module_name:
        continue

    # Only wrapping functions for now because it's not obvious what wrapping
    # classes or other callables might mean.
    if not _isfunction(_thing):
        continue

    _glbls[_thing_name] = _pretty_assert_for(_thing)
