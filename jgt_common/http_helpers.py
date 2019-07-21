"""Tools for simplifying HTTP requests and responses."""

from contextlib import contextmanager
from itertools import chain
import json

import requests

from . import build_classification_rst_string, classify, no_op


MAX_CALL_FAILURES = 5

MAX_ERROR_MESSAGE_CONTENT_LENGTH = 500

HEADERS_TO_IGNORE_IN_ERROR_MESSAGE = [
    "Accept-Encoding",
    "Connection",
    "Content-Length",
    "User-Agent",
    "X-Auth-Token",
]

STATUS_CODE_RANGES = {
    "a successful response": (200, 300),
    "a client error": (400, 500),
    "a server error": (500, 600),
    "any error": (400, 600),
}


@classify("json", "response")
def safe_json_from(response, description=""):
    """
    Accept a response object and attempts to return the JSON-decoded data.

    Args:
        response (requests.models.Response): a Response object from a requests call
        description (str, optional): details about the response expected.

    Returns:
        The JSON-decoded data from the response

    Raises:
        AssertionError: if the JSON data cannot be decoded properly.

    """
    # the json module in py2 doesn't contain the specific error,
    # and instead throws a generic ValueError
    try:
        decode_error = json.decoder.JSONDecodeError
    except AttributeError:
        decode_error = ValueError
    try:
        data = response.json()
    except decode_error:
        content = list(
            filter(
                None,
                [
                    description,
                    "URL: {}".format(response.url),
                    "Status Code: {}".format(response.status_code),
                    "Response Text -{}-".format(response.text),
                ],
            )
        )
        message = format_items_as_string_tree(
            "\nResponse Content NOT a Valid JSON:", content
        )
        raise AssertionError(message)
    return data


@classify("response")
def get_data_from_response(
    response, dig_layers=None, check_empty=True, first_only=True
):
    """
    Accept a response object and returns a dict of the data contained within.

    Args:
        response (requests.models.Response): A Response object from a requests call
        dig_layers (list): List of keys to "dig" down into the response before returning
        check_empty (bool): If True, raises an AssertionError if the payload is empty
        first_only (bool): Strip the list wrapping the data and return the first result

    Returns:
        The data payload.

    Examples:
        >>> response.json() == {"data": [{"key": "value"}, {"key": "value2"}],
                                "other": ""}
        True
        >>>
        >>> get_data_from_response(response, dig_layers=['data'])
        {'key': 'value'}
        >>> get_data_from_response(response, dig_layers=['data'], first_only=False)
        [{'key': 'value'}, {'key': 'value2'}]
        >>> get_data_from_response(response, dig_layers=['other'])
        AssertionError: Payload was empty: ''
        >>> get_data_from_response(response, dig_layers=['other'], check_empty=False)
        ""

    """
    # most common response is a 'list' of only one element, so first_only=True
    # will fix that by default, but allows a toggle to get full data if desired.
    data = safe_json_from(response)
    if isinstance(data, (int, str, bool)):
        return data
    dig_layers = dig_layers or []
    for layer in dig_layers:
        if layer in data:
            data = data[layer]
    if first_only and isinstance(data, list):
        data = data[0]
    if check_empty:
        assert data, "Payload was empty: {}".format(data)
    return data


@classify("response")
def get_data_list(response, **kwargs):
    """
    Get the full list of data from within a response, if the data is a list.

    Helper around get_data_for_response that returns the full list of data
    if the data is in a list format, rather than the default of returning
    the first object inside the list.

    For ``**kwargs`` values and more information, see :py:func:`get_data_from_response`.
    """
    kwargs.update(first_only=False)
    return get_data_from_response(response, **kwargs)


def _indent_items(*items):
    r"""
    Indent all items recursively.

    Adds a tab to every item in ``*items``. If the item is a list, this function
    will be recursively called with the contents of that list, adding an additional
    tab stop.  Each additional nested list will result in an additional tab for every
    item in that additional list.

    Returns:
        list: The items given, with all nested items having an added indent.

    Examples:
        >>>_indent_items('ex1', ['nested1', 'nested2', ['double1'], ['double2']])
        ['\tex1', '\t\tnested1', '\t\tnested2', '\t\t\tdouble1', '\t\t\tdouble2']

    """
    return [
        "\t{}".format(s)
        for x in items
        for s in chain(_indent_items(*x) if isinstance(x, list) else [x])
    ]


@classify("string")
def format_items_as_string_tree(*items):
    """
    Format the items provided as a string representing a "tree" format.

    Any lists or nested lists will be flattened, with each level of nested lists
    getting its own level of indentation. Each item, once flattened with the
    appropriate level of indentation provided, will be placed on its own line.

    Returns:
        str: An indented "tree" format of the items.

    Example:
        >>> format_items_as_string_tree('ex1', 'ex2', ['nested1', 'nested2',
        >>>                             ['double1'], ['double2']], 'ex3')
            ex1
            ex2
                nested1
                nested2
                    double1
                    double2
            ex3

    """
    return "\n".join(_indent_items(*items))


def _status_code_from(status_description):
    if isinstance(status_description, int):
        return status_description
    return requests.codes.get(status_description.replace(" ", "_").upper())


@classify("status_code")
def is_status_code(expected_status_description, actual_status_code):
    """
    Determine if a given status code matches the expected result.

    Args:
        expected_status_description (str, int): The result to match. Can be:
            - A Python requests libarary status reason ("OK")
            - A phrase matching a ``_status_code_ranges`` key ('a client error')
            - An integer for the response status code (404)
        actual_status_code (int): the status code from the response to be validated

    Returns:
        bool: Whether or not the actual status code matches the expected description.

    Raises:
        AssertionError: if an invalid ``expected_status_description`` value is provided.

    """
    if expected_status_description in STATUS_CODE_RANGES:
        # a range descriptor was provided
        lower, upper = STATUS_CODE_RANGES[expected_status_description]
        return lower <= actual_status_code < upper

    # Convert description to code if not provided as code
    expected_code = _status_code_from(expected_status_description)
    message = 'Coding error, unknown status code check "{}"'.format(
        expected_status_description
    )
    assert expected_code, message
    return expected_code == actual_status_code


@classify("string", "response")
def create_error_message(summary_line, request, response_content, additional_info=None):
    """
    Create a detailed error message based on an API call.

    This message will include information about the request and response,
    cutting off the response content at the set ``MAX_ERROR_MESSAGE_CONTENT_LENGTH``.
    Additional information can be included in the message by including the
    ``additional_info`` parameter.

    Args:
        summary_line (str): The first line of the message that describes the error.
        request (Request): The python requests library Request.
        response_content (str): The response content to be included in the response.
        additional_info (dict): A dictionary containing additional information to be
            included in the message. The keys and values will be separated by a
            ``":"`` in the message. (optional)

    Returns:
        str: The complete and detailed error message.

    """
    if additional_info is None:
        additional_info = {}

    headers = {
        header: value
        for header, value in request.headers.items()
        if header not in HEADERS_TO_IGNORE_IN_ERROR_MESSAGE
    }

    response_content = str(response_content)[:MAX_ERROR_MESSAGE_CONTENT_LENGTH]
    request_body = str(request.body)[:MAX_ERROR_MESSAGE_CONTENT_LENGTH]

    return format_items_as_string_tree(
        summary_line,
        [
            "Request Info:",
            [
                "Url: {}".format(request.url),
                "HTTP Method: {}".format(request.method),
                "Headers: {}".format(headers),
                "Body: {}".format(request_body),
            ],
        ],
        ["{}: {}".format(k, v) for k, v in additional_info.items()],
        ["Response Content: {}".format(response_content)],
    )


@classify("status_code", "response")
def check_response_status_code(
    expected_status_description, response, call_description=None, additional_info=None
):
    """
    Check that a response's status code matches an expected status description.

    Args:
        expected_status_description (str, int): The expected HTTP response status
            reason or code.
        response (Response): The python requests library response to validate.
        call_description (str): additional details about the call placed (optional)
        additional_info (dict): Additional Info to be passed to create_error_message

    Returns:
        str: Empty string if response status code matches, or a detailed error message
            otherwise

    """
    if is_status_code(expected_status_description, response.status_code):
        return ""
    try:
        response_content = json.dumps(safe_json_from(response), indent=4)
    except AssertionError:
        response_content = response.content

    status_message = "{} - Actual Response Status: {}"
    info = {
        "Expected Status": status_message.format(
            expected_status_description, response.status_code
        ),
        "Reason": response.reason,
    }
    info.update(additional_info or {})
    if call_description:
        info.update({"Call Description": call_description})
    err_msg = create_error_message(
        summary_line="The response status does not match the expected status.",
        request=response.request,
        response_content=response_content,
        additional_info=info,
    )
    return err_msg


@classify("status_code", "response")
def validate_response_status_code(
    expected_status_description, response, err_prefix="", **kwargs
):
    """
    Assert that a response's status code matches an expected status code.

    Args:
        expected_status_description (str, int): The expected HTTP response status reason
            or code.
        response (Response): The python requests library response to validate.
        err_prefix (str, optional): Prefix, if any, to the error message, when an
            assertion is raised.
        kwargs: additional keyword args to be passed on to check_response_status_code.

    Raises:
        AssertionError: if the response status validation fails

    """
    err_msg = check_response_status_code(
        expected_status_description, response, **kwargs
    )
    if err_msg:
        raise AssertionError(err_prefix + err_msg)


@classify("status_code", "response")
def response_if_status_check(
    call_description, response, target_status="a successful response"
):
    """
    Validate a response matches the expected status code before returning.

    Args:
        call_description (str): Text description of the call placed
            (e.g. "get schedule list")
        response (requests.Response): the response object to validate.
        target_status (str, int): The expected HTTP response status reason or code.

    Returns:
        requests.Response: if the response status validation succeeds

    Raises:
        AssertionError: if the response status validation fails

    """
    validate_response_status_code(
        target_status,
        response,
        call_description='Call to "{}" failed'.format(call_description),
    )
    return response


@classify("response")
def safe_request_validator(
    inner_validator, max_failures=MAX_CALL_FAILURES, logger=None
):
    """
    Wrap a ``check_request_until`` validator in additional response checks.

    Will "fail fast" in the case of an ``unauthorized`` response,
    and will support retrying calls if a non-200-level reponse status is returned.

    Args:
        inner_validator (function): case-specific response validator function,
            should return False if condition is not met and re-checking should continue,
            or True if target status is complete and result should be returned.
        max_failures (int): total number of retries *per cycle* a call should be allowed
            before failing permanently and returning the last response
        logger (logging.logger, optional): a logger to handle debug messages from the
            validator

    Returns:
        function: response-status-checking decorated version of ``inner_validator``

    """
    debug = logger.debug if logger else no_op
    # In Python 3+, modification of outer scope variables is achievable
    # with the ``nonlocal`` keyword,
    # but for 2.7 compatibility, we must access and modify via a dictionary.
    failures = {"fail_count": 0}

    def inner(response):
        if is_status_code("unauthorized", response.status_code):
            return True
        if max_failures and not is_status_code(
            "a successful response", response.status_code
        ):
            failures["fail_count"] += 1
            if failures["fail_count"] <= max_failures:
                return False
            msg = "***Call failed {} times, final status code was {}."
            debug(msg.format(failures["fail_count"], response.status_code))
        failures["fail_count"] = 0
        return inner_validator(response)

    return inner


@classify("logging")
@contextmanager
def call_with_custom_logger(call, curl_logger):
    """
    Context Manager to make a call with a given curl_logger in place of the default.

    If curl_logger is a last-only logger, call ``.done()`` on context exit.
    NOTE: for last-only loggers, the log will not be written until you exit the context.

    Example:
        Create a new callable based on 'call' that uses the logger 'logger_to_use'::

            with call_with_custom_logger(call, logger_to_use) as call_using_logger:
                some_result = check_until(call_using_logger, ...)
    """
    curl_logger = curl_logger() if isinstance(curl_logger, type) else curl_logger

    def custom_call(*args, **kwargs):
        return call(*args, curl_logger=curl_logger, **kwargs)

    yield custom_call

    if hasattr(curl_logger, "done"):
        curl_logger.done()


__doc__ += build_classification_rst_string(
    globals(),
    __name__,
    {
        "json": "JSON related functions",
        "logging": "Logging related functions",
        "response": "Requests' Response object related functions",
        "status_code": "HTTP Status code functions",
        "string": "String related functions",
    },
)
