"""
General helper functions.

.. inheritance-diagram:: jgt_common
   :parts: 1

----

The functions and classes in this module fall into several
general categories:
"""

from __future__ import print_function
import ast
from collections import defaultdict
import itertools as _itertools
import logging
import os as _os
from math import nan

import pkg_resources
import random
import shutil as _shutil
import string as _string
import subprocess as _subprocess
import sys as _sys
import time as _time

import wrapt as _wrapt


_logger = logging.getLogger(__name__)
_debug = _logger.debug


_CLASSIFICATION_ATTRIBUTE = "classify_data"
"""Attribute used to store classification data on functions and classes."""


def classify(*args):
    """Add glossary subject category classification meta-data to it's target."""

    def classifier(target):
        setattr(target, _CLASSIFICATION_ATTRIBUTE, args)
        return target

    return classifier


# classify itself deserves to be classified.
# Since it can't be used as a regular decorator on itself, handle it here:
classify = classify("doc", "meta-data")(classify)

class_lookup = {}
"""
This dictionary is to allow code that needs to have very late binding of a class
to look up the class here, and code that needs to control another module's use of a
late bound class to set it in this dictionary.

Code accessing this dictionary should use ``.get()`` with a default value so that
`this` module doesn't have to import lots of things here to set up all the defaults.
Code accessing this dictionary should publish which key(s) it will be using so that
modules wishing to retarget those classes will know which keys to set.

Code setting values in this dictionary so do so `before` importing modules that
will use that value. Setting values in this dictionary is only needed when the
default values need to be changed.

(Motivation: the requests client logging code needs to be able to use a custom
class instead of just ``requests.Session`` when being used by testing code
with the Locust test runner, and it uses this dictionary to accomplish this.)

"""

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'


CHECK_UNTIL_TIMEOUT = 300
CHECK_UNTIL_CYCLE_SECS = 5


_TICKET_INFO = defaultdict(dict)
for data in pkg_resources.iter_entry_points("tag_to_url"):
    _TICKET_INFO[data.name].update(data.load())


OBSOLETE_TICKETING_SYSTEMS = [
    key for key, meta_data in _TICKET_INFO.items() if not meta_data.get("url_template")
]
"""Systems for which we still support identifying Tickets, but no longer can access."""


# Don't require user/embedder of this to use re.IGNORECASE
HEX_DIGIT_RE = r"[\da-fA-F]"
"""Regular expression for matching a single hex digit."""


def re_for_hex_digits(length):
    """Return regular expression for matching exactly ``length`` hex digits."""
    return HEX_DIGIT_RE + "{" + str(length) + "}"


UUID_BASIC_RE = "-".join(map(re_for_hex_digits, [8, 4, 4, 4, 12]))
"""
Regular expression (RE) for matching UUID string forms.

This RE is not anchored, or delimited, for maximum reuse.
"""

UUID_ISOLATED_RE = r"\b{}\b".format(UUID_BASIC_RE)
"""RE for matching an UUID that is not part of a larger "word"."""


@classify("misc")
def no_op(*args, **kwargs):
    """Reusable no-op function."""
    pass


@classify("misc")
def always_true(*args, **kwargs):
    """Return True regardless of any provided arguments."""
    return True


@classify("misc")
def always_false(*args, **kwargs):
    """Return False regardless of any provided arguments."""
    return False


@classify("misc")
def identity(x, *args):
    """
    Build simple identity function based on provided parameters.

    A single parameter is returned as is, multiple parameters are returned as a tuple.

    From https://stackoverflow.com/questions/8748036/is-there-a-builtin-identity-function-in-python  # noqa: E501
    Not the top voted answer, but it handles both single and multiple parameters.
    """
    return (x,) + args if args else x


@classify("files", "meta-data")
def display_name(path, package_name=""):
    """
    Create a human-readable name for a given project.

    Determine the display name for a project given a path and (optional) package name.
    If a display_name.txt file is found, the first line is returned. Otherwise, return a
    title-cased string from either the base directory or package_name (if provided).

    Args:
        path (str): Path for searching
        package_name (str): Sphinx-style, dot-delimited package name (optional)

    Returns:
        str: A display name for the provided path

    """
    name_path = _os.path.join(path, "display_name.txt")
    if _os.path.exists(name_path):
        with open(name_path, "r") as name_fo:
            return name_fo.readline().rstrip("\r\n")
    raw_name = package_name.split(".")[-1] if package_name else _os.path.basename(path)
    return _string.capwords(raw_name.replace("_", " "))


@classify("misc", "string")
def format_if(format_str, content):
    """
    Return a message string with a formatted value if any content value is present.

    Useful for error-checking scenarios where you want a prepared error message
    if failures are present (passed in via content), or no message if no failures.

    Args:
        format_str (str): A message string with a single format brace to be filled
        content (str): A value to be filled into the format_str if present

    Returns:
        str: either the format_str with content included if content present,
        or an empty string if no content.

    """
    return format_str.format(content) if content else ""


@classify("misc")
def default_if_none(value, default):
    """
    Return ``default if value is None else value``.

    Use because:
      * no chance of the value stutter being mistyped, speeds up code reading time.
      * easier to read when value or default are complex expressions.
      * can save having to create local variable(s) to shorten the
        ``if .. is None ...`` form.

    """
    return default if value is None else value


@classify("sequence")
def no_nones(iterable):
    """Return a list of the non-None values in iterable."""
    return [x for x in iterable if x is not None]


@classify("sequence")
def truths_from(iterable):
    """Return a list of the truthy values in iterable."""
    return list(filter(None, iterable))


@classify("sequence")
def padded_list(iterable, size, padding=None):
    """
    Generate a fixed-length list from an iterable, padding as needed.

    Args:
        iterable (iterable): Any iterable that needs padding
        size (int): The length for the returned list
        padding: Any value that should be used to pad an iterable that is too short

    Returns:
        list: The iterable parameter converted to a list, up to size, padded as needed.

    """
    return list(
        _itertools.islice(_itertools.chain(iterable, _itertools.repeat(padding)), size)
    )


def _python_2_or_3_base_str_type():
    try:
        return basestring
    except NameError:
        return str


@classify("misc", "sequence")
def is_iterable(item):
    """
    Return True if item is iterable, False otherwise, using an iter(item) test.

    From the Python documentation for class :py:class:`collections.abc.Iterable`:

        Checking isinstance(obj, Iterable) detects classes that are registered as
        Iterable or that have an __iter__() method, but it does not detect classes that
        iterate with the __getitem__() method.
        *The only reliable way to determine whether an object is iterable is to call
        iter(obj)*.
    """
    try:
        iter(item)
        return True
    except TypeError:
        return False


@classify("sequence")
def list_from(item):
    """
    Generate a list from a single item or an iterable.

    Any item that is "false-y", will result in an empty list. Strings and dictionaries
    will be treated as single items, and not iterable.

    Args:
        item: A single item or an iterable.

    Returns:
        list: A list from the item.

    Examples:
        >>> list_from(None)
        []
        >>> list_from('abcd')
        ['abcd']
        >>> list_from(1234)
        [1234]
        >>> list_from({'abcd': 1234})
        [{'abcd': 1234}]
        >>> list_from(['abcd', 1234])
        ['abcd', 1234]
        >>> list_from({'abcd', 1234})
        ['abcd', 1234]

    """
    if not item:
        return []
    if isinstance(item, (_python_2_or_3_base_str_type(), dict)) or not is_iterable(
        item
    ):
        return [item]
    return list(item)


@classify("sequence", "string")
def string_to_list(source, sep=",", maxsplit=-1, chars=None):
    """``.split()`` a string into a list and ``.strip()`` each piece.

    For handling lists of things, from config files, etc.

    Args:
        source (str): the source string to process
        sep (str, optional): The ``.split`` ``sep`` (separator) to use.
        maxsplit (int, optional): The ``.split`` ``maxsplit`` parameter to use.
        chars (str, optional): The ``.strip`` ``chars`` parameter to use.

    """
    return [item.strip(chars) for item in source.split(sep, maxsplit)]


@classify("exit")
def cleanup_and_exit(dir_name=None, status=0, message=None):
    """
    Cleanup a directory tree that was created and exit.

    Args:
        dir_name (string): Full path to a directory to remove (optional)
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error (optional)

    """
    if dir_name:
        _shutil.rmtree(dir_name)
    exit(status=status, message=message)


@classify("exit", "running commands")
def safe_run(commands, cwd=None):
    """
    Run the given list of commands, only return if no error.

    If there is an error in attempting or actually running the commands,
    error messages are printed to stdout and ``sys.exit()`` will be called.
    """

    try:
        status = _subprocess.call(commands, cwd=cwd)
    except OSError as e:
        print("")
        print('Error when trying to execute: "{}"'.format(" ".join(commands)))
        print("")
        print(e)
        _sys.exit(-1)

    if status:
        print("")
        print('Error {} from running: "{}"'.format(status, " ".join(commands)))
        print("")
        _sys.exit(status)


@classify("exit")  # noqa: A001
def exit(status=0, message=None):  # noqa: A001
    """
    Exit the program and optionally print a message to standard error.

    Args:
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error (optional)

    """
    if message:
        print(message, file=_sys.stderr)
    _sys.exit(status)


@classify("exit")
def error_if(check, status=None, message=""):
    """
    Exit the program if a provided check is true.

    Exit the program if the check is true. If a status is provided, that code is used
    for the exit code; otherwise the value from the check is used. An optional message
    for standard error can also be provided.

    Args:
        check: Anything with truthiness that can check if the program should exit or not
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error if check is True (optional)

    """
    if check:
        exit(status=status or check, message=message.format(check))


@classify("dict", "filter")
def filter_dict(a_dict, keep_key=always_true, keep_value=always_true):
    """
    Filter a dictionary based on truthiness.

    Return a new dict based on keeping only those keys _and_ values whose function
    returns True.

    Args:
        a_dict (dict): A dictionary to filter values from.
        keep_key (function): Return True if the key is to be kept.
        keep_value (function): Return True if the value is to be kept.

    Returns:
        dict: A new dictionary with only the desired key, value pairs.

    """
    return {k: v for k, v in a_dict.items() if keep_key(k) and keep_value(v)}


@classify("dict", "filter")
def dict_strip_value(a_dict, value=None):
    """
    Return a new dict based on stripping out any key with the given value.

    Note:
        The default value ``None`` is chosen because it is a common case.
        Unlike other functions, value ``None`` is literally the value ``None``.

    Args:
        a_dict (dict): A dictionary to strip values from.
        value: Any value that should be stripped from the dictionary.

    Returns:
        dict: A new dictionary without key/value pairs for the given value.

    """
    return filter_dict(a_dict, keep_value=lambda v: v != value)


@classify("dict", "filter")
def dict_transform(a_dict, key_transform=identity, value_transform=identity):
    """
    Return a new dict based on transforming the keys and/or values of ``a_dict``.

    Args:
        a_dict (dict): the source dictionary to process
        key_transform (function): Takes a key and returns a new key to use.
        value_transform (function): Takes a value and returns a new value to use.

    Returns:
        dict: A new dictionary with keys and values as transformed.

    """
    return {key_transform(k): value_transform(v) for k, v in a_dict.items()}


@classify("dict", "filter")
def dict_from(iterable, key_transform=identity, value_transform=identity):
    """
    Build a new dict based on turning values from an iterable into key/value pairs.

    Example:
        A common use case would be to build a dict from a list of values,
        using the list values as keys,
        and building dict values as a transform from the list values.::

            > l = [1, 2, 3, 4, 5]
            > result = dict_from(l, value_transform=lambda n: n**2)
            # {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

    Args:
        iterable (iterable): the source for the dictionary to be created
        key_transform (function): Takes a key and returns a new key to use.
        value_transform (function): Take a value and returns a new value to use.

    Returns:
        dict: A new dictionary with key and values as transformed.

    """
    return {key_transform(x): value_transform(x) for x in iterable}


@classify("misc", "ticketing system")
def ticketing_system_for(ticket):
    """Return the Ticketing System/Type for the given ticket, or the empty string."""
    for ticket_system, info in _TICKET_INFO.items():
        if info["pattern"].match(ticket):
            return ticket_system
    return ""


@classify("misc", "ticketing system")
def url_for_ticket(ticketing_system, ticket):
    """
    Return a URL for the given ticketing_system, ticket pair.

    Does NOT validate that ticket string "looks" like a ticket for the ticketing system.

    Raises if ticketing_system is not a supported system.
    """
    system_dict = must_get_key(_TICKET_INFO, ticketing_system)
    return system_dict.get("url_template", "").format(ticket)


@classify("misc", "ticketing system")
def url_if_ticket(ticket):
    """
    Return a Ticket URL if a ticket is found.

    Args:
        ticket (string): Possible ticket ID

    Returns:
        string: Either a URL if a string is found, otherwise an empty string.

    """

    ticket_system = ticketing_system_for(ticket)
    if ticket_system:
        return url_for_ticket(ticket_system, ticket)
    return ""


@classify("random", "string")
def generate_random_string(prefix="", suffix="", size=8, choose_from=None):
    """
    Generate a random string of the specified size.

    Args:
        prefix (str, optional): String to prepend to the beginning of the random string.
        suffix (str, optional): String to append to the end of the random string.
        size (int, optional): Number of characters the random string should have.
            (defaults to 8)
        choose_from (str): A string containing the characters from which the randomness
            will be chosen. If not provided, it will choose from lowercase letters and
            digits.

    Returns:
        str: A randomly generated string.

    Raises:
        AssertionError: if the given length is incompatible with prefix/suffix length

    Examples:
        >>> generate_random_string()
        'vng345jn'
        >>> generate_random_string(prefix='Lbs-', suffix='-test', size=15)
        'Lbs-js7eh9-test'
        >>> generate_random_string(prefix='Lbs-', size=15)
        'Lbs-js7eh98sfnk'
        >>> generate_random_string(suffix='-test', size=15)
        '8sdfjs7eh9-test'
        >>> generate_random_string(choose_from="aeiou")
        'uiiaueea'

    """
    choose_from = default_if_none(choose_from, _string.ascii_lowercase + _string.digits)
    rand_string_length = size - len(prefix) - len(suffix)
    message = '"size" of {} too short with prefix {} and suffix {}!'
    assert rand_string_length > 0, message.format(size, prefix, suffix)
    rand_string = "".join(random.choice(choose_from) for _ in range(rand_string_length))
    return "{}{}{}".format(prefix, rand_string, suffix)


@classify("sequence")
def index_or_default(a_list, value, default=-1):
    """
    Return the index of a value from a list, or a default if not found.

    Args:
        a_list (list): A list from which to find the index
        value (any): the list item whose index is sought
        default (any): the value to return if the value is not in the list

    Returns:
        int,any: an index value (int) for the list item, or default value (any)

    """
    return a_list.index(value) if value in a_list else default


@classify("exit", "environment")
def must_be_in_virtual_environment(
    exit_code=1, message="Must be running in a Python virtual environment, aborting!"
):
    """
    Ensure the current process is running in a virtual environment.

    Args:
        exit_code (int, optional): Exit code to use if not running in a virtual
            environment.
        message (string, optional): Message to print if not running in a virtual
            environment.

    """
    if "VIRTUAL_ENV" not in _os.environ:
        exit(exit_code, message)


@classify("dict")
def must_get_key(a_dict, key):
    """
    Either return the value for the key, or raise an exception.

    The exception will indicate what the valid keys are.
    Inspired by Gherkin steps so that a typo in the Gherkin
    will result in a more helpful error message than the stock KeyError.

    Args:
        a_dict (dict): Dictionary with the values
        key (str): The key whose value is desired

    Returns:
        The value found on the key

    Raises:
        KeyError: if the given key is not present in the dictionary.

    """
    if key not in a_dict:
        raise KeyError(
            "{} is not one of: {}".format(key, ", ".join(sorted(map(str, a_dict))))
        )
    return a_dict[key]


@classify("dict")
def must_get_keys(a_dict, *keys):
    """
    Either return the value found for the keys provided, or raise an exception.

    Args:
        a_dict (dict): Dictionary with the values
        keys (str): The key or keys whose value is desired

    Returns:
        The value found on the final key

    Raises:
        KeyError: if any of the given keys are not present in the dictionary.

    """
    for key in keys:
        a_dict = must_get_key(a_dict, key)
    return a_dict


@classify("environment")
def var_from_env(var_name):
    """
    Try to get a value from an environment variable.

    Get an environment variable and raise an error if not set / has an empty value.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: if the variable name is not set or has an empty value.

    """
    envvar = _os.environ.get(var_name)
    if not envvar:
        raise ValueError('"{}" variable not found!'.format(var_name))
    return envvar


@classify("files")
def get_file_contents(*paths):
    """
    Get the contents of a file as a Python string.

    Args:
        *paths: All paths that lead to the file whole contents are to be retrieved.

    Returns:
        str: The contents of the file.

    """
    with open(_os.path.join(_os.path.join(*paths)), "r") as f:
        return f.read()


@classify("files", "meta-data")
def get_file_docstring(file_path):
    """
    Get the full docstring of a given python file.

    Args:
        file_path (str): The path to the file whose docstring should
            be gathered and returned.

    Returns:
        str: The python file's docstring.

    """
    tree = ast.parse(get_file_contents(file_path))
    return ast.get_docstring(tree)


@classify("files", "filter")
def filter_lines(line_filter, lines, return_type=None):
    """
    Filter the given lines based on the given filter function.

    This function by default will return the same type that it is given.
    If you'd like, you may return a different type by providing the
    ``return_type`` parameter.

    The expected values for the the ``lines`` parameter type and the
    ``return_type`` value are ``str`` and ``list``. Any other types/values
    may cause unexpected behavior.

    Args:
        line_filter (Callable): The callable function to be used to filter each line.
            It should take a single string parameter and return a boolean.
        lines (Union[str, List[str]]): Either a string with newline characters splitting
            the lines, or a list of lines as strings.
        return_type (type): The desired return type. If not provided, the type of the
            ``lines`` parameter will be used.

    Returns:
        Union[str, List[str]]: The filtered lines.

    """
    if return_type is None:
        return_type = type(lines)

    if isinstance(lines, _python_2_or_3_base_str_type()):
        lines = lines.split("\n")

    filtered_lines = list(filter(line_filter, lines))
    return filtered_lines if return_type is list else "\n".join(filtered_lines)


@classify("misc")
def fib_or_max(fib_number_index, max_number=None):
    """
    Get the nth Fibonacci number or max_number, which ever is smaller.

    This can be used for retrying failed operations with progressively longer
    gaps between retries, cap'd at the max_number paraemter if given.
    """
    current, next_ = 0, 1
    for _ in range(fib_number_index):
        current, next_ = next_, current + next_
        if max_number and current > max_number:
            return max_number
    return current


DEFAULT_MAX_RETRY_SLEEP = 30


@classify("looping", "exceptions")
def retry_on_exceptions(
    max_retry_count, exceptions, max_retry_sleep=DEFAULT_MAX_RETRY_SLEEP
):
    """
    Retry a function based on provided parameters.

    A wrapper to retry a function max_retry_count times if any of the given exceptions
    are raised.

    In the event the exception/exceptions are raised, this code will sleep for ever
    increasing amounts of time (using the fibonacci sequence) but capping at
    max_retry_sleep seconds.

    Args:
        max_retry_count (int): The maximum number of retries, must be > 0..
        exceptions (exception or tuple of exceptions): The exceptions to catch and
            retry on.
        max_retry_sleep (int, float): The maximum time to sleep between retries.
    """
    assert exceptions, "No exception(s) given"
    assert max_retry_count > 0, "max_retry_count must be greater than 0"

    @_wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        error_count = 0
        while error_count <= max_retry_count:
            try:
                return wrapped(*args, **kwargs)
            except exceptions as e:
                error = e
                _debug('Retry on exception: "{}" encountered during call'.format(error))
                error_count += 1
                retry_sleep = fib_or_max(error_count, max_number=max_retry_sleep)
                _debug("...trying again after a sleep of {}".format(retry_sleep))
                _time.sleep(retry_sleep)
        _debug(
            "Retry on exception: Max Retry Count of {} Exceeded".format(max_retry_count)
        )
        raise error

    return wrapper


@classify("looping", "exceptions", "class")
class IncompleteAtTimeoutException(Exception):
    """
    Exception for check_until results that timeout still pending validation.

    Args:
        msg (str): Human readable string describing the exception.
        call_result (any): the final result of the call, which failed validation.
        timeout (int,float): the timeout at which the result was still failing.

    Atributes:
        call_result (any): the final result of the call, which failed validation.
        timeout (int,float): the timeout at which the result was still failing.

    """

    def __init__(self, msg, call_result=None, timeout=None):
        self.call_result = call_result
        self.timeout = timeout
        super(IncompleteAtTimeoutException, self).__init__(msg)


@classify("looping")
def check_until(
    function_call,
    is_complete_validator,
    timeout=CHECK_UNTIL_TIMEOUT,
    cycle_secs=CHECK_UNTIL_CYCLE_SECS,
    logger=_logger,
    fn_args=None,
    fn_kwargs=None,
):
    """
    Periodically call a function until its result validates or the timeout is exceeded.

    Args:
        function_call (function): The function to be called
        is_complete_validator (function): a fn that will accept the output from
            function_call and return False if the call should continue repeating (still
            pending result), or True if the checked result is complete and may be
            returned.
        timeout (int): maximum number of seconds to "check until" before raising an
            exception.
        cycle_secs (int): how long to wait (in seconds) in between calls to
            function_call.
        logger (logging.logger, optional): a logging instance to be used for debug info,
            or ``None`` to suppress logging by this function.
        fn_args (tuple, optional): tuple of positional args to be provided to
            function_call
        fn_kwargs (dict, optional): keyword args to be provided to function_call

    Returns:
        any: the result of function_call when the is_complete_validator returns any True
            value.

    Raises:
        jgt_common.IncompleteAtTimeoutException: if function_call's result never
            satisfies the is_complete_validator before timeout is reached.

    """
    fn_args = fn_args or ()
    fn_kwargs = fn_kwargs or {}
    debug = logger.debug if logger else no_op

    check_start = _time.time()
    end_time = _time.time() + timeout

    while True:
        result = function_call(*fn_args, **fn_kwargs)
        if is_complete_validator(result):
            time_elapsed = round(_time.time() - check_start, 2)
            debug("Final response achieved in {} seconds".format(time_elapsed))
            return result
        if _time.time() > end_time:
            break
        _time.sleep(cycle_secs)
    # If a result wasn't returned from within the while loop,
    # we have reached timeout without a valid result.
    msg = "Response was still pending at timeout."
    debug(msg)
    raise IncompleteAtTimeoutException(msg, call_result=result, timeout=timeout)


@classify("misc", "exceptions")
def assert_if_values(format_if_format, error_fun=lambda x: "\n".join(truths_from(x))):
    """
    Assert if any truthy values are returned (or yielded) from the decorated function.

    Any values that the decorated function yields/returns are passed to ``error_fun``.
    ``format_if_format``, and the result of the ``error_fun`` call,
    are passed to ``format_if``.
    The result of the ``format_if`` call is used for an assertion.

    Args:
        format_if_format (str): the first parameter to format_if.
        error_fun (callable): called on the results of the decorated function,
            return value will be passed as the 2nd parameter to format_if.
            The default function will only process truthy values.
            That can be changed by passing in your own custom ``error_fun``

    Returns:
        None - If no values are returned, or yielded,
        or the result of ``error_fun`` is falsey, return None.

    Raises:
        AssertionError: as described above.

    This decorator is meant to simplify code that otherwise has to manually keep
    track of a list of things to complain about::

        errors = []
        for thing in things:
           if bad(thing):
               errors.append(description_of(thing))
        err_msg = format_if("blah blah blah: {}", "".join(errors))
        assert not err_msg, err_msg

    into simpler code::

        @assert_if_values("blah blah blah: {}")
        ...
            for thing in things:
                if bad(thing):
                    yield description_of(thing)

    """

    @_wrapt.decorator
    def helper(wrapped, instance, args, kwargs):
        err_msg = format_if(format_if_format, error_fun(wrapped(*args, **kwargs)))
        assert not err_msg, err_msg

    return helper


@classify("misc", "sequence")
def accumulator_for(fun):
    """
    Accumulate the results of calling fun into a unique list, returning that list.

    Everytime the decorated function is called, its results are appended
    to a list, and that list is returned instead.
    Each invocation of this function results in a wrapper that uses its own
    unique list.

    NOTE: If you use this is as a decorator on a function definition,
    ALL invocations of the function will accumulate into a single list.
    This is probably not what you want.

    The intent is to use this decorator "as needed"::

        def get_thing_when_stable():
            '''
            Get a thing when the API returns a stable result.

            A stable result is when 3 consecutive payloads match.
            If no stable result is achieved, an IncompleteAtTimeoutException exception
            is raised.
            '''
            results = check_until(accumulator_for(api_get_thing), last_3_payloads_equal)
            return get_thing_from_payload(results[-1])

    """
    # NOTE: Not using wrapt; it would add another level of nesting / complexity,
    #       for dynamic run-time wrapping of a function.
    #       If we find that this is used for decorating function definitions,
    #       this decision about using wrapt can be changed without affecting
    #       the users of this function.

    results_list = []

    def wrapped_fun(*args, **kwargs):
        results_list.append(fun(*args, **kwargs))
        return results_list

    return wrapped_fun


@classify("sequence")
def only_item_of(item_sequence, label=""):
    """Assert item_sequence has only one item, and return that item."""
    label = label or item_sequence.__class__.__name__
    assert len(item_sequence) == 1, '{} was not of length 1: "{}"'.format(
        label, item_sequence
    )
    return item_sequence[0]


@classify("sequence", "class")
class NotEmptyList(list):
    """
    A list that fails to iterate if it is empty.

    Iterating on this list will fail if the list is empty.
    This simplifies code from having to check for empty lists everywhere.
    Empty lists are a problem because ``for`` loop bodies don't execute on empyt lists.
    thus any checks/tests/etc in a loop body would not run.
    In a testing context, the loop would "succeed" by not doing anything
    (it would fail to have checked anything) and that would be a false-positive.
    """

    @staticmethod
    def error_on_empty():
        """Is called to return the error message when the NotEmptyList is empty."""
        return "list is empty!"

    def __iter__(self):
        """
        Iterate only if not empty.

        Any loops that check items in the list could fail to fail for empty
        lists becuase the loop body would never execute.
        Help our clients by asserting if the list is empty so they don't have to.
        """
        assert self, self.error_on_empty()
        return super(NotEmptyList, self).__iter__()


@classify("sequence", "class")
class CommonAttributeList(list):
    """
    A list for similar objects that can be operated on as a group.

    Accessing an attribute on this list instead
    returns a list of that attribute's value from each member.
    (unless the attribute is defined here or in the base class)
    If any member of this list does not have that attribute, ``AttributeError`` is
    raised.

    Setting an attribute on this list instead sets the attribute on each member.
    """

    def __getattr__(self, name):
        """Get the named attribute from all items in the list."""
        try:
            return [getattr(x, name) for x in self]
        except AttributeError:
            message = 'Attribute "{}" not present on all list items.'
            raise AttributeError(message.format(name))

    def __setattr__(self, name, value):
        """On each item, set the give attribute to the given value."""
        for item in self:
            setattr(item, name, value)

    def update_all(self, **kwargs):
        """Update all attributes based on the provided kwargs."""
        for key, value in kwargs.items():
            setattr(self, key, value)


@classify("requests", "class")
class ResponseInfo(object):
    """
    Keep track of needed info about test operation responses (or any info really).

    Originally created to augment/track info about ``requests'`` responses, it's not
    limited or bounded by that use case.
    Please read ``response`` more generally as any kind of object useful for catpuring
    some kind of response from the system under test.
    In addition, arbitrary other attributes can be set on this object.
    To make that easier, ``kwargs`` is processed as attribute / value pairs to be set on
    the object, for whatever attributes make sense for your application.

    Sometimes this object is keeping track of a response that is needed,
    but isn't available yet.
    In these cases, ``response_callback`` can be set to a parameter-less function that
    can be called to obtain the response when the ``response_data`` property is used.

    For ease of use, when the data is buried in the response or otherwise needs to be
    decoded, ``response_data_extract`` can be used. It should take one parameter (the
    response) and return the desired data from it. This function should not have any
    side-effects. ``response_data_extract`` is also used by the ``response_data``
    property, see that property documentation for details.

    Args:
        response (any, optional): Whatever kind of response object needs tracking.
        description (str, optional): Description of this particular response.
        response_callback (function w/no parameters, optional):
            A callback to use in place of the ``response`` field.
        response_data_extract (function w/1 parameter, optional):
            A callback used to extract wanted data from the response.
        kwargs (dict, optional): any additional attributes to set on this object,
            based on the name/value pairs in kwargs.

    """

    def __init__(
        self,
        response=None,
        description=None,
        response_callback=None,
        response_data_extract=None,
        **kwargs,
    ):

        super(ResponseInfo, self).__init__()

        self.response = response
        self.description = description
        self.response_callback = response_callback
        self.response_data_extract = response_data_extract
        for key, value in kwargs.items():
            setattr(self, key, value)

    def run_response_callback(self):
        """Run the ``response_callback``, if any, and set ``response`` to the result.

        Set ``response_callback`` to None so iit isn't run more than once.
        """
        if self.response_callback:
            self.response = self.response_callback()
            self.response_callback = None

    @property
    def response_data(self):
        """
        Property that returns the data from a response.

        1. If ``response_callback`` is set, that is used to obtain the response,
           otherwise the ``response`` attribute is used.
           If the ``response_callback`` is called,
           it's result is assigned to the ``.response`` attribute and
           the ``response_callback`` attribute is set to None.
           This is to prevent the callback from being invoked more than once.
        2. If ``response_data_extract`` is set, it is called on the response
           from step 1, and it's return value is the value of this property.
           Otherwise the result of step 1 is returned as is.
           Note that in this step the ``.response`` attribute is not changed,
           the ``response_data_extract`` callback is expected to have no side-effects.
        """
        self.run_response_callback()
        if self.response_data_extract:
            return self.response_data_extract(self.response)
        return self.response


@classify("requests", "class")
class ResponseList(NotEmptyList, CommonAttributeList):
    """
    A list specialized for testing, w/ResponseInfo object items.

    To best understand this class, it is important to have
    a strong understanding of :py:class:`CommonAttributeList` and
    :py:class:`ResponseInfo`.
    The common workflow for ``ResponseList`` relies greatly on those other connected
    pieces.

    For example, you might utilize this class in a ways such as this::

        >>> responses = ResponseList()
        >>> responses.build_and_set(response=client.get_thing())
        >>>
        >>> # All the `.response` fields, see `CommonAttributeList`
        >>> for response in responses.response:
        ...     assert response.json()["thing"]
        >>>
        >>>
        >>> responses.set(
        ...     ResponseInfo(response=client.get_thing(param),
                             description=f"Getting {param}...")
        ...     for param in my_params
        ... )
    """

    def set(self, resp):  # noqa: A003
        """
        Clear and set the contents of this list to single object / iterator of objects.

        Generators will be converted into a list to allow access more than once.

        This method can be handy/useful when transforming this list's contents
        from one form to another, such as:

        >>> x = CommonAttributeList()
        >>> ...
        >>> x.set(transform(thing, doo_dad) for thing in x)
        """
        self[:] = list_from(resp)

    @property
    def single_item(self):
        """Property - Assert this list has one item, and return that item."""
        return only_item_of(self)

    def build_and_set(self, *args, **kwargs):
        """
        Create object and then set it on the list.

        Create ResponseInfo object with args & kwargs, then ``.set`` it on this
        ResponseList.
        """
        self.set(ResponseInfo(*args, **kwargs))

    def run_response_callbacks(self):
        """Call ``run_response_callback`` on each item of this ReponseList."""
        for resp_info in self:
            resp_info.run_response_callback()


@classify("misc", "class")
class Flag(object):
    """
    A settable, nameable Boolean flag.

    Instances can be used in a boolean context (if/while/etc.)

    Call the instance to set a new value, returning the previous value.

    ``.value`` to access the value.
    ``.name`` to access the name.

    Motivation:
    Importing a boolean value from another module makes a new binding;
    changing the imported binding does not change the imported-from-modules value.
    Additionally, this gives you a nice named value for str() and repr(),
    and a clean way to handle assigning new values and toggling existing values.

    Typical use might be::

        limit_thing = Flag(initial_value=False, name="Limit size of thing")

    In the Command line processing code::

        limit_thing(args.limit_thing)

    Off in some module::

        def do_thing():
            ...
            loop_size = LIMITED_SIZE if limit_thing else MAX_SIZE
            ...

    Use an instance of this class where you want semantic control over code
    without having to expose implementation details of that code
    to the control point;
    keeping the determination of, say, "running smoke tests,"
    or "running in a deployment pipeline," or "running in a PR checker,"
    separate from how the code will react to that condition.
    """

    def __init__(self, initial_value=False, name="Flag"):
        self._value = bool(initial_value)
        self._name = name

    def __call__(self, new_value):  # noqa: D102
        old_value, self._value = self._value, bool(new_value)
        return old_value

    def toggle(self):
        """Flip to the opposite value, return the old value."""
        return self(not self)

    @property
    def value(self):  # noqa: D102
        return self._value

    @property
    def name(self):  # noqa: D102
        return self._name

    def __str__(self):  # noqa: D105
        return f"{self.name}->{self.value}"

    def __repr__(self):  # noqa: D105
        return (
            f"<{self.__class__.__name__}"
            f"(initial_value={self.value}, name={self.name!r})>"
        )

    def __bool__(self):
        """
        Instances are useable in boolean contexts.

        See https://docs.python.org/3/reference/datamodel.html#object.__bool__
        """
        return self.value


@classify("doc")
def first_line_of_doc_string(thing):
    """
    Get the first non-empty line of the doc string for thing, if there is one.

    If thing is a class and has no doc string,
    return the first line of the __init__ method doc string if there is one.
    """

    doc_string = getattr(thing, "__doc__", None)
    if doc_string is None:
        __init__method = getattr(thing, "__init__", None)
        if __init__method:
            return first_line_of_doc_string(__init__method)
        return ""
    doc_string_lines = list(filter(None, doc_string.splitlines()))
    return doc_string_lines[0].strip()


@classify("doc")
def build_classification_rst_string(from_dict, for_module, category_name_mappings):
    """
    Create rST for all the items in from_dict that are part of for_module.

    Example:
        __doc__ += build_classification_rst_string(globals(), __name__, <category
                   mappings dict>)

        The ``for_module`` parameter is needed because often ``globals()``
        contains symbols imported from other modules not be documented here.

    Args:
        from_dict (dict): A dictionary of name to function/class mappings,
            such as from locals() or globals()
        for_module (str): The module for which rST documentation is desired.
        category_name_mappings (str): Map from the short hand names used in the
            :py:func:`classify` decorator to the desired category table label.

    Returns:
        str: multiline rST string.

    """
    classification_mapping = defaultdict(list)
    for name, item in sorted(from_dict.items()):
        if getattr(item, "__module__", None) != for_module:
            continue
        classify_data = getattr(item, _CLASSIFICATION_ATTRIBUTE, None)
        if classify_data is None:
            continue
        # The built-in csv module doesn't expose any way to quote CSV data without
        # writing it to a file, and certainly not in rST's csv table format, so we
        # protect the CSV here with a simple quote-mark replacement if/until a better
        # csv option comes along.
        csv_line = '   :py:func:`{}`, "{}"'.format(
            name, first_line_of_doc_string(item).replace(DOUBLE_QUOTE, SINGLE_QUOTE)
        )
        for group in classify_data:
            classification_mapping[group].append(csv_line)
    if not classification_mapping:
        return "<NO classifications were found>"
    result = "\n\n"
    for category, items in sorted(classification_mapping.items()):
        result += ".. csv-table:: {}\n".format(category_name_mappings[category])
        result += "   :widths: auto\n"
        result += "\n"
        result += "\n".join(items)
        result += "\n\n"

    result += "\n---------\n\n"
    return result


@classify("misc")
def percent_diff(a, b, precision=2):
    """Get percentage difference, out to ``precision`` places."""
    if a == b:
        return 0
    elif a == 0 or b == 0:
        return nan
    # It is debatable whether this is the correct choice for determining
    # relative difference. min(), max(), and the mean all have a case to be made for
    # them, both with and without abs(). See, e.g.:
    # https://en.wikipedia.org/wiki/Relative_change_and_difference#Definitions
    return round(abs((a - b) / max(abs(a), abs(b))) * 100, precision)


# Define this here because it is needed by the other scripts.
def execute_command_list(commands_to_run, verbose=True):
    """
    Execute each command in the list.

    If any command fails, print a helpful message and exit with that status.
    """
    for command in commands_to_run:
        readable_command = " ".join(command)
        try:
            if verbose:
                print(readable_command)
            _subprocess.check_call(command)
        except _subprocess.CalledProcessError as e:
            print(
                '"{}" - returned status code "{}"'.format(
                    readable_command, e.returncode
                )
            )
            exit(e.returncode)
        except FileNotFoundError as f:
            print(
                '"{}" - No such file/program: "{}"'.format(readable_command, f.filename)
            )
            exit(2)


__doc__ += build_classification_rst_string(
    globals(),
    __name__,
    {
        "class": "Classes Defined in this Module",
        "dict": "Dictionary related functions",
        "doc": "Documentation support",
        "environment": "Environment related functions",
        "exceptions": "Exceptions and exception handling",
        "exit": "Exitting the process",
        "files": "File and file contents related functions",
        "filter": "Filtering and Transforming functions",
        "looping": "Looping / Retry related items",
        "meta-data": "Meta-data related functions",
        "misc": "Miscellaneous functions",
        "random": "Random data related functions",
        "requests": "Classes/functions for working with the ``requests`` library",
        "running commands": "Subprocesses/Commands related functions",
        "sequence": "Sequences/Lists helper classes and functions",
        "string": "String related functions",
        "ticketing system": "Ticketing System related functions",
    },
)
