"""Convenience functions for doing asserts with helpful names and helpful messages."""
from jgt_common import percent_diff
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
    """Assert the values to not be equal."""
    assert expected != actual, _msg_concat(
        msg, "Expected '{}' to be not equal to actual '{}'".format(expected, actual)
    )


def eq(expected, actual, msg=""):
    """Assert the values are equal."""
    assert expected == actual, _msg_concat(
        msg, "Expected '{}' == actual '{}'".format(expected, actual)
    )


def less(a, b, msg=""):
    """Assert that a < b."""
    assert a < b, _msg_concat(msg, "Expected '{}' < '{}'".format(a, b))


def less_equal(a, b, msg=""):
    """Assert that a <= b."""
    assert a <= b, _msg_concat(msg, "Expected '{}' <= '{}'".format(a, b))


def greater(a, b, msg=""):
    """Assert that a > b."""
    assert a > b, _msg_concat(msg, "Expected '{}' > '{}'".format(a, b))


def greater_equal(a, b, msg=""):
    """Assert that a >= b."""
    assert a >= b, _msg_concat(msg, "Expected '{}' >= '{}'".format(a, b))


def is_in(value, sequence, msg=""):
    """Assert that value is in the sequence."""
    assert value in sequence, _msg_concat(
        msg, "Expected: '{}' to be in '{}'".format(value, sequence)
    )


def any_in(a_sequence, b_sequence, msg=""):
    """Assert at least one member of a_sequence is in b_sequence."""
    assert any(a in b_sequence for a in a_sequence), _msg_concat(
        msg, "None of: '{}' found in '{}'".format(a_sequence, b_sequence)
    )


def not_in(item, sequence, msg=""):
    """Assert item is not in sequence."""
    assert item not in sequence, _msg_concat(
        msg, "Did NOT Expect: '{}' to be in '{}'".format(item, sequence)
    )


def is_not_none(a, msg=""):
    """Assert a is not None."""
    assert a is not None, _msg_concat(msg, "'{}' should not be None".format(a))


def is_not_empty(sequence, msg=""):
    """
    Semantically more helpful than just ``assert sequence``.

    Sequences and containers in python are False when empty, and True when not empty.
    This helper reads better in the test code and in the error message.
    """
    assert sequence, _msg_concat(msg, "'{}' - should not be empty".format(sequence))


def is_close(a, b, msg="", **isclose_kwargs):
    """Assert that math.isclose returns True based on the given values."""
    assert _isclose(a, b, **isclose_kwargs), _msg_concat(
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
    """Assert that actual and expected are within `places` equal."""
    # Set relative tolerance to 0 because we don't want that messing up the places check
    relative_tolerance = 0
    absolute_tolerance = 10.0 ** (-places)
    assert _isclose(
        expected, actual, rel_tol=relative_tolerance, abs_tol=absolute_tolerance
    ), _msg_concat(
        msg, "Expected '{}' to be almost equal to '{}'".format(actual, expected)
    )


def is_singleton_list(sequence, item_description="something", msg=""):
    """Make sure the sequence has exactly one item (of item_description)."""
    assert len(sequence) == 1, _msg_concat(
        msg,
        "Expected to find a one item list of {} but found '{}' instead".format(
            item_description, sequence
        ),
    )


def is_instance(value, of_type, msg=""):
    """Assert value is instance of of_type."""
    assert isinstance(value, of_type), _msg_concat(
        msg,
        "Got value '{}' of type '{}' when expecting something of type {}".format(
            value, type(value), of_type
        ),
    )
