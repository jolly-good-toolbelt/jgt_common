"""
Unit tests for the qecommon_tools assert helpers.

These are simple functions being tested, so the tests are pretty simple too.
"""

import pytest
from qecommon_tools import assert_


def test_equality_asserts():
    assert_.eq(1, 1)
    assert_.eq(range(10), range(10))
    assert_.eq(dict(), {})  # noqa: C408
    with pytest.raises(AssertionError):
        assert_.eq(set(), {})


def test_not_equality_asserts():
    assert_.not_eq(1, 2)
    assert_.not_eq(set(), dict())  # noqa: C408
    with pytest.raises(AssertionError):
        assert_.not_eq(1, 1)


def test_less_asserts():
    assert_.less(0, 1)
    assert_.less((1, 2), (2, 10))
    assert_.less((1, 2), (1, 3))
    with pytest.raises(AssertionError):
        assert_.less(1, 1)


def test_less_equal_asserts():
    assert_.less_equal(1, 1)
    assert_.less_equal((1, 3), (1, 3))
    with pytest.raises(AssertionError):
        assert_.less_equal(2, 1)


def test_greater_asserts():
    assert_.greater(1, -3)
    assert_.greater((3, 0), (2, 10))
    assert_.greater((1, 3), (1, 1))
    with pytest.raises(AssertionError):
        assert_.greater(1, 1)


def test_greater_equal_asserts():
    assert_.greater_equal(1, 1)
    assert_.greater_equal((1, 3), (1, 3))
    with pytest.raises(AssertionError):
        assert_.greater_equal(0, 1)


def test_is_in_asserts():
    assert_.is_in("w", "qwerty")
    assert_.is_in(1, range(1, 4))
    assert_.is_in(
        "me",
        {"do": "a deer", "re": "A drop of golden sun", "me": "a name I call myself"},
    )
    with pytest.raises(AssertionError):
        assert_.is_in(0, range(1, 4))


def test_any_in_asserts():
    assert_.any_in("2asdf", "qwerty4fun2behappy")
    assert_.any_in(range(-4, 5), range(4, 10))
    assert_.any_in(range(-4, 4), range(-6, -3))
    with pytest.raises(AssertionError):
        assert_.any_in(range(-4, 4), range(-6, -4))


def test_not_in_asserts():
    assert_.not_in("a", "qwerty")
    assert_.not_in(0, range(1, 4))
    assert_.not_in(
        "fa",
        {"do": "a deer", "re": "A drop of golden sun", "me": "a name I call myself"},
    )
    with pytest.raises(AssertionError):
        assert_.not_in(1, range(1, 4))


def test_is_not_none_asserts():
    assert_.is_not_none("")
    assert_.is_not_none(set())
    assert_.is_not_none([])
    with pytest.raises(AssertionError):
        assert_.is_not_none(None)


def test_is_not_empty_asserts():
    assert_.is_not_empty("something here")
    assert_.is_not_empty({1, 2})
    assert_.is_not_empty(range(1, 2))
    with pytest.raises(AssertionError):
        assert_.is_not_empty({})


def test_almost_equal_asserts():
    assert_.almost_equal(1, 1)
    assert_.almost_equal(1.01, 1.015)
    assert_.almost_equal(1.01, 1.02, places=1)
    with pytest.raises(AssertionError):
        assert_.almost_equal(2.005, 2.006, places=4)


def test_is_singleton_list_asserts():
    assert_.is_singleton_list("a")
    assert_.is_singleton_list(range(0, 1))
    assert_.is_singleton_list([3])
    with pytest.raises(AssertionError):
        assert_.is_singleton_list([])
    with pytest.raises(AssertionError):
        assert_.is_singleton_list(range(0, 2))


def test_is_instance_asserts():
    assert_.is_instance(1, int)
    assert_.is_instance(ValueError(), Exception)
    assert_.is_instance(KeyError(), (int, Exception))
    assert_.is_instance(42, (int, Exception))
    with pytest.raises(AssertionError):
        assert_.is_instance(42, Exception)


def test_is_close_asserts():
    assert_.is_close(100, 97, rel_tol=0.03)
    with pytest.raises(AssertionError):
        assert_.is_close(100, 96, rel_tol=0.03)
