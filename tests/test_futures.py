"""Unit tests for the jgt_common.futures tools."""

import concurrent
import random
import time

import pytest
from jgt_common import futures
from jgt_common import ResponseInfo
from jgt_common import ResponseList

# Arbitrary concurrent.futures pool size to use for testing
POOL_SIZE_FOR_TESTING = random.randint(3, 7)


def do_work(x):
    """
    Return any arbitrary unique value based on x.

    Unique so that set operations can be used to check future results without
    concern for the order of the operations.
    """
    # Sleep a few milliseconds to allow thread interleaving
    # but not too long in order to keep test runs short.
    time.sleep(random.random() / 100.0)
    return 30 * x


# Arbitrary re-usable iterable of inputs to test against.
inputs = range(10)

# The expected results given all the inputs to do_work.
desired_results = set(map(do_work, inputs))


@pytest.fixture
def executor():
    """
    Make sure an executor is setup for testing.

    By using this as a fixture, tests can be run in any order
    as only the first use will create the executor.

    Tests probably won't use the executor parameter,
    but could if they wanted to.
    """
    futures.set_thread_pool_size(POOL_SIZE_FOR_TESTING)
    return futures.get_executor()


def test_set_thread_pool_size():
    """Test that seeting the thread pool size works."""
    # Limits here are arbitrary
    pool_size = POOL_SIZE_FOR_TESTING + random.randint(5, 10)
    old_size = futures._MAX_WORKERS
    assert futures._MAX_WORKERS != pool_size
    futures.set_thread_pool_size(pool_size)
    assert futures._MAX_WORKERS == pool_size
    futures._MAX_WORKERS = old_size


def test_get_executor_raises_when_no_thread_pool_size_set():
    """What it says in this test function's name."""
    # Limits here are arbitrary
    old_size = futures._MAX_WORKERS
    old_executor = futures._THREADPOOL_EXECUTOR
    futures._MAX_WORKERS = None
    futures._THREADPOOL_EXECUTOR = None

    with pytest.raises(TypeError):
        futures.get_executor()

    futures._MAX_WORKERS = old_size
    futures._THREADPOOL_EXECUTOR = old_executor


def test_primitives(executor):
    """Test run_each and as_completed_result since they're meant for each other."""
    d = futures.run_each(inputs, do_work)
    assert set(inputs) == set(d.values())
    assert set(map(type, d.keys())) == {concurrent.futures.Future}
    assert desired_results == set(futures.as_completed_result(d))


def test_set_each(executor):
    """Test set_each and set_when_completed by implication."""
    work_items = ResponseList(
        ResponseInfo(input=x, expected=do_work(x)) for x in inputs
    )
    futures.set_each(work_items, "result", lambda r: do_work(r.input))
    assert work_items.expected == work_items.result


def test_set_response_on_each(executor):
    """Test set_response_on_each and set_response_when_completed by implication."""
    work_items = ResponseList(
        ResponseInfo(input=x, expected=do_work(x)) for x in inputs
    )
    futures.set_response_on_each(work_items, lambda r: do_work(r.input))
    assert work_items.expected == work_items.response


def test_result_from_each(executor):
    results = futures.result_from_each(inputs, do_work)
    assert desired_results == set(results)


def test_as_completed_item_result(executor):
    fdict = futures.run_each(inputs, do_work)
    results = dict(futures.as_completed_item_result(fdict))
    assert set(inputs) == results.keys()
    assert desired_results == set(results.values())
