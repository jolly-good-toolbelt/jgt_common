"""
Convenience functions for doing checks with helpful names and helpful messages.

All the functions in this module return the empty string("") when the check passes
and a description of how the check has failed when it fails.
This is intentional so that the truthyness of strings and falsyness of empty strings
can be exploited for use with ``format_if`` or ``assert`` or ...
"""

# NOTE TO IMPLEMENTORS:
# While this module is stand-alone, it is also intended to work with
# sibling module ``assert_``.
# As such a number of conventions are expected of the code here:
# 1 Keep to the promise made in the doc string above about strings and truthyness.
# 2 Use the word "Check" at the start of the doc string so that the ``assert_`` module
#   can make a sensible substituion.
# 3 Any function defined in this module without a leading underscore honors #1.
# 4 Corrollary to #3, any function starting with a leading underscore is internal to
#   this module.
# 5 If any classes are defined in this module, they will not be processed by ``assert_``
#   and may or may not need a hand written version in that module.
# 6 If we ever switch to using __all__ for controlling what functions we export,
#   the ``assert_`` module  will need to be changed.
# 7 There are no direct self-tests for this module because everything here
#   is tested via the ``assert_`` module's tests.
#   New functions added here should have new assertion tests in tests/test_asserts.py

from . import percent_diff
from . import format_if as _format_if

try:
    from math import isclose as _isclose
except ImportError:
    # noqa E501 From: https://stackoverflow.com/questions/5595425/what-is-the-best-way-to-compare-floats-for-almost-equality-in-python/5595453
    def _isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def _msg_concat(prefix, body):
    """Join with a space if prefix isn't empty."""
    return "{} {}".format(prefix, body) if prefix else body


def not_eq(expected, actual, msg=""):
    """Check that the values are not equal."""
    if expected != actual:
        return ""
    return _msg_concat(
        msg, "Expected '{}' to be not equal to actual '{}'".format(expected, actual)
    )


def eq(expected, actual, msg=""):
    """Check that the values are equal."""
    if expected == actual:
        return ""
    return _msg_concat(msg, "Expected '{}' == actual '{}'".format(expected, actual))


def less(a, b, msg=""):
    """Check that a < b."""
    if a < b:
        return ""
    return _msg_concat(msg, "Expected '{}' < '{}'".format(a, b))


def less_equal(a, b, msg=""):
    """Check that a <= b."""
    if a <= b:
        return ""
    return _msg_concat(msg, "Expected '{}' <= '{}'".format(a, b))


def greater(a, b, msg=""):
    """Check that a > b."""
    if a > b:
        return ""
    return _msg_concat(msg, "Expected '{}' > '{}'".format(a, b))


def greater_equal(a, b, msg=""):
    """Check that a >= b."""
    if a >= b:
        return ""
    return _msg_concat(msg, "Expected '{}' >= '{}'".format(a, b))


def is_in(value, sequence, msg=""):
    """Check that value is in the sequence."""
    if value in sequence:
        return ""
    return _msg_concat(msg, "Expected: '{}' to be in '{}'".format(value, sequence))


def any_in(a_sequence, b_sequence, msg=""):
    """Check that at least one member of a_sequence is in b_sequence."""
    if any(a in b_sequence for a in a_sequence):
        return ""
    return _msg_concat(
        msg, "None of: '{}' found in '{}'".format(a_sequence, b_sequence)
    )


def not_in(item, sequence, msg=""):
    """Check that item is not in sequence."""
    if item not in sequence:
        return ""
    return _msg_concat(msg, "Did NOT Expect: '{}' to be in '{}'".format(item, sequence))


def is_not_none(a, msg=""):
    """Check a is not None."""
    if a is not None:
        return ""
    return _msg_concat(msg, "'{}' should not be None".format(a))


def is_not_empty(sequence, msg=""):
    """
    Cheeck that sequence is not empty.

    Semantically more descriptive than just testing sequence for truthyness.

    Sequences and containers in python are False when empty, and True when not empty.
    This helper reads better in the test code and in the error message.
    """
    if sequence:
        return ""
    return _msg_concat(msg, "'{}' - should not be empty".format(sequence))


def is_close(a, b, msg="", **isclose_kwargs):
    """Check that math.isclose returns True based on the given values."""
    if _isclose(a, b, **isclose_kwargs):
        return ""
    return _msg_concat(
        msg,
        "Expected '{}' to be close to '{}', "
        "but they differ by '{}', a difference of '{}%'.{}".format(
            a,
            b,
            abs(a - b),
            percent_diff(a, b),
            _format_if(": kwargs: {}", isclose_kwargs),
        ),
    )


def almost_equal(actual, expected, places=2, msg=""):
    """Check that actual and expected are within `places` equal."""
    # Set relative tolerance to 0 because we don't want that messing up the places check
    relative_tolerance = 0
    absolute_tolerance = 10.0 ** (-places)
    if _isclose(
        expected, actual, rel_tol=relative_tolerance, abs_tol=absolute_tolerance
    ):
        return ""
    return _msg_concat(
        msg, "Expected '{}' to be almost equal to '{}'".format(actual, expected)
    )


def is_singleton_list(sequence, item_description="something", msg=""):
    """Check that the sequence has exactly one item (of item_description)."""
    if len(sequence) == 1:
        return ""
    return _msg_concat(
        msg,
        "Expected to find a one item list of {} but found '{}' instead".format(
            item_description, sequence
        ),
    )


def is_instance(value, of_type, msg=""):
    """Check that value is an instance of of_type."""
    if isinstance(value, of_type):
        return ""
    return _msg_concat(
        msg,
        "Got value '{}' of type '{}' when expecting something of type {}".format(
            value, type(value), of_type
        ),
    )
