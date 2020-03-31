"""
Helpful functions for using concurrent.futures with a shared thread pool executor.

Terminology:

  * fdict - futures dictionary - as in the examples for the concurrent.futures
    module documentation, a dictionary whose keys are futures and whose values
    are related to the work being done. See each function for details on what
    the values will be.

Purpose:

   These helpers are meant to be used for "spot" parallelism,
   not for whole application parallelism. In places where the code needs to do
   a whole bunch of slow things that can be done in parallel (API calls, etc)
   and then "goes synchronous again."  (Testing is one such use case.)


Archicture:

   One executor thread pool is used by all of these functions.
   To support the use of these functions in a "library" kind of way,
   configuring the size of the thread pool and shutting it down (if ever used)
   are done by calling separate functions. This is so an application can use
   configuration data for the set up without having to spread knowledge of that
   configuration data to any function(s) that want to use these functions.

   The executor thread pool defined here is mainly meant for use by the other
   functions defined here, but users of this module are free to use it themselves
   directly as needed.

"""

from concurrent.futures import ThreadPoolExecutor as _ThreadPoolExecutor
from concurrent.futures import as_completed  # noqa - imported for pass-through use.
from concurrent.futures import wait  # noqa - imported for pass-through use.

_THREADPOOL_EXECUTOR = None
_MAX_WORKERS = None


def set_thread_pool_size(max_workers):
    """Set the size for the shared ThreadPoolExecutor."""

    global _MAX_WORKERS
    _MAX_WORKERS = max_workers


# Implemenation note:
# This function is _not_ memoized:
# If no executor is ever created, the shutdown function doesn't need to do anything.
# If the only way to get at the executor was via this function,
# then shutdown might create an executor just to shut it down.
def get_executor():
    """
    Get the shared ThreadPoolExecutor.

    Returns:
        ThreadPoolExecutor: the shared thread pool executor.

    Raises:
        TypeError: if set_thread_pool_size() was not called first.

    """

    global _THREADPOOL_EXECUTOR
    if _THREADPOOL_EXECUTOR is None:
        if _MAX_WORKERS is None:
            raise TypeError("set_thread_pool_size() has to be called first.")
        _THREADPOOL_EXECUTOR = _ThreadPoolExecutor(max_workers=_MAX_WORKERS)
    return _THREADPOOL_EXECUTOR


def shutdown_executor():
    """If a ThreadPoolExecutor was started, shut it down."""

    if _THREADPOOL_EXECUTOR is None:
        return
    _THREADPOOL_EXECUTOR.shutdown(wait=True)


def run_each(iterable, func):
    """
    Call func on each item in iterable, using a future.

    The returned fdict's futures (keys of the fdict) may or may not be completed
    by the time this function returns. It is up to the caller to decide how to harvest
    the results from the futures.

    Can be used directly, but is mostly used under the covers
    by the other functions in this module.

    Args:
        iterable (any): Any iterable.
        func (callable): will be called with one item from iterable.

    Returns:
        fdict: Mapping from a future to the item from iterable used to make it.

    """

    executor = get_executor()
    return {executor.submit(func, item): item for item in iterable}


def set_response_when_completed(fdict):
    """Set '.response' on each value from fdict to the future's result."""

    for future in as_completed(fdict):
        fdict[future].response = future.result()


def set_response_on_each(iterable, func):
    """
    Shorthand for set_response_when_completed(run_each(iterable, func)).

    This was a common enough pattern to warrant a helper for clarity and brevity,
    and is primarily for those using jgt_common's ResponseList and ResponseInfo objects.

    Example:
        Instead of writing::

            for item in work_list:
                item.response = client.do_work(item.input)

        New code that parallelizes that work::

            set_response_on_each(work_list, lambda item: client.do_work(item.input))

    """

    set_response_when_completed(run_each(iterable, func))


def set_when_completed(field, fdict):
    """Set the given `field` on each value from fdict to that future's result."""

    for future in as_completed(fdict):
        setattr(fdict[future], field, future.result())


def set_each(iterable, field, func):
    """
    Set `field` on each item of iterable to the value of func, when it completes.

    Shorthand for set_when_completed(field, run_each(iterable, func)).

    A more general form of set_response_on_each.
    """

    set_when_completed(field, run_each(iterable, func))


def as_completed_result(futures):
    """Yield future.result() from futures, as each future completes."""

    for future in as_completed(futures):
        yield future.result()


def result_from_each(iterable, func):
    """
    Shorthand for as_completed_result(run_each(iterable, func)).

    This was a common enough pattern to warrant a helper for clarity and brevity.

    When you want all the results from calling func on the items from the iterable,
    but you don't need to know which result came from which item or in which order.
    """

    yield from as_completed_result(run_each(iterable, func))


def as_completed_item_result(fdict):
    """
    Yield (item, future.result()) from fdict, as each future completes.

    The values in the tuples are returnd in that order to allow this function
    to be used to create a dict mapping an item to its result::

        futures = run_each(iterable, func)
        results_map = dict(as_completed_item_result(futures))
    """

    for future in as_completed(fdict):
        yield fdict[future], future.result()
