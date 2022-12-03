from typing import Any

import os
import sys
import io
import sys
import logging
import collections
import contextlib
import dataclasses
import inspect
import tempfile

# Check if supported external packages are installed
# NOTE: These are not required, but will be used during formatting if found.
try:
    from requests import Request, PreparedRequest, Response
    from requests.exceptions import RequestException

    _has_requests_package = True
except (NameError, ModuleNotFoundError):
    Request = Any
    Response = Any
    RequestException = Exception
    _has_requests_package = False


_logger = logging

_global_package_name = None
_global_dump_path = None
_global_dump_locals = False


# NOTE: Support for colors will be added for Windows later.
_LOG_FMT = "[ {asctime}.{msecs:04.0f}  \33[1m{levelname}\33[0m  {name} ]  {message}"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"
_DUMP_MSG = "".join(
    (
        "\n\n",
        "\33[1m" if sys.platform != "win32" else "",
        'Dumped stack and locals to "{name}"',
        "\33[0m" if sys.platform != "win32" else "",
        "\nCopy and paste the following to view:\n\n    cat '{name}'\n",
    )
)


class Yogger(logging.Logger):
    def _log_with_stack(self, level: int, *args: tuple, **kwargs: dict):
        super().log(level, *args, **kwargs)

        # Dump current stack if 'dump_locals' was set to True
        if _global_dump_locals:
            stack = inspect.stack()
            if len(stack) > 2:
                name = _dump(stack[2:][::-1], e=None, dump_path=None)
                super().log(level, _DUMP_MSG.format(name=name))

    def warning(self, *args: tuple, **kwargs: dict):
        self._log_with_stack(logging.WARNING, *args, **kwargs)

    def error(self, *args: tuple, **kwargs: dict):
        self._log_with_stack(logging.ERROR, *args, **kwargs)

    def critical(self, *args: tuple, **kwargs: dict):
        self._log_with_stack(logging.CRITICAL, *args, **kwargs)

    def log(self, level: int, *args: tuple, **kwargs: dict):
        if level >= logging.WARNING:
            self._log_with_stack(level, *args, **kwargs)
        else:
            super().log(level, *args, **kwargs)


def install() -> None:
    """Install the Yogger Logger Class and Instantiate the Global Logger"""
    logging.setLoggerClass(Yogger)

    global _logger
    _logger = logging.getLogger(__name__)


def _requests_request_repr(name: str, request: Request) -> str:
    """Representation of a requests.Request Object

    Args:
        name (str): Name of the Requests response.
        request (requests.Request): Request object, prepared by the Requests module.

    Returns:
        str: Formatted representation of a requests.Request object.
    """
    req_repr = ""
    req_repr += f"{name} = {request!r}"
    req_repr += f"\n  {name}.method = {request.method}"
    req_repr += f"\n  {name}.url = {request.url}"
    req_repr += f"\n  {name}.headers = \\"
    for field in request.headers:
        req_repr += f'\n    {field} = {_repr("_", request.headers[field])}'

    for attr in ("body", "params", "data"):
        if hasattr(request, attr) and getattr(request, attr):
            req_repr += f"\n  {name}.{attr} = "
            req_repr += _repr("_", getattr(request, attr)).replace("\n", "\n  ")

    return req_repr


def _requests_response_repr(
    name: str,
    response: Response,
    *,
    with_history: bool = True,
) -> str:
    """Representation of a requests.Response Object

    Args:
        name (str): Name of the Requests response.
        response (requests.Response): Response object from the Requests module.
        with_history (bool): Include the request redirect history in the representation (not yet accessable to user). Defaults to True.

    Returns:
        str: Formatted representation of a requests.Response object.
    """
    resp_repr = ""
    resp_repr += f"{name} = {response!r}"
    resp_repr += f"\n  {name}.url = {response.url}"
    resp_repr += f"\n  {name}.request = "
    resp_repr += _repr("_", response.request).replace("\n", "\n  ")
    if with_history and response.history:
        resp_repr += f"\n  {name}.history = ["
        for prev_resp in response.history:
            resp_repr += "\n    "
            resp_repr += _requests_response_repr("_", prev_resp, with_history=False).replace("\n", "\n    ")

        resp_repr += "\n  ]"

    resp_repr += f"\n  {name}.status_code = {response.status_code}"
    resp_repr += f"\n  {name}.headers = \\"
    for field in response.headers:
        resp_repr += f'\n    {field} = {_repr("_", response.headers[field])}'

    resp_repr += f'\n  {name}.content = {_repr("_", response.content)}'
    return resp_repr


def _requests_exception_repr(name: str, e: RequestException) -> str:
    """Formatted Representation of a requests.exceptions.RequestException

    Args:
        name (str): Name of the Requests Exception.
        e (requests.exceptions.RequestException): Requests exception to represent.

    Returns:
        str: Formatted representation of a Requests exception.
    """
    e_repr = ""
    e_repr += f"{name} = {e!r}"
    e_repr += "\n  " + _repr(f"{name}.request", e.request).replace("\n", "\n  ")
    e_repr += "\n  " + _repr(f"{name}.response", e.response).replace("\n", "\n  ")
    return e_repr


def _repr(name: str, value: Any) -> str:
    """Formatted Representation of a Variable's Name and Value

    Args:
        name (str): Name of the variable to represent.
        value (Any): Value to represent.

    Returns:
        str: Formatted representation of a variable.
    """
    if _has_requests_package:
        # Support for Requests package
        if type(value) is Response:
            return _requests_response_repr(name, value)

        if type(value) in (PreparedRequest, Request):
            return _requests_request_repr(name, value)

        if isinstance(value, RequestException):
            return _requests_exception_repr(name, value)

    if isinstance(value, dict):
        # Multiline representation of dictionary
        return f"{name} = <{type(value).__module__}.{type(value).__name__}>\n  " + "\n  ".join(_repr(f"{name}[{k!r}]", v).replace("\n", "\n  ") for k, v in value.items())

    if isinstance(value, (list, tuple, collections.deque)) and not all(isinstance(v, (int, str)) for v in value):
        # Multiline representation of list, tuple, and deque
        return f"{name} = <{type(value).__module__}.{type(value).__name__}>\n  " + "\n  ".join(_repr(f"{name}[{i}]", v).replace("\n", "\n  ") for i, v in enumerate(value))

    if dataclasses.is_dataclass(value):
        # Multiline representation of dataclass
        return f"{name} = <{type(value).__module__}.{type(value).__name__}>\n  " + "\n  ".join(
            _repr(f"{name}.{f.name}", f.name) + " = " + _repr(f"{name}.{f.name}", getattr(value, f.name)).replace("\n", "\n  ") for f in dataclasses.fields(value)
        )

    # Representation of other object
    other_repr = f"{name} = {value!r}"

    # Indent if it is multiline
    if "\n" in other_repr:
        return "\\\n  " + other_repr.replace("\n", "\n  ")

    return other_repr


def _exception_dumps(e: Exception) -> str:
    """Create a String Representation of an Exception

    Args:
        e (Exception): Exception that was raised.

    Returns:
        str: Representation of the stack.
    """
    e_repr = ""
    e_repr += "Exception:\n"
    e_repr += f"  {type(e).__module__}.{type(e).__name__}: {e!s}\n"
    e_repr += f"  args: {e.args!r}\n"
    e_repr += "\n"
    return e_repr


def _stack_dumps(
    stack: list[inspect.FrameInfo],
    package_name: str | None = None,
) -> str:
    """Create a String Representation of Frames in a Stack

    Args:
        stack (list[inspect.FrameInfo]): Stack to represent.
        package_name (str, optional): Name of the package to dump from the stack, otherwise non-exclusive if set to None. Defaults to None.

    Returns:
        str: Representation of the stack.
    """
    stack_repr = ""
    modules = [inspect.getmodule(frame_record[0]) for frame_record in stack]
    for i, (module, frame_record) in enumerate(zip(modules, stack)):
        if module is None:
            # Moduleless frame, e.g. dataclass.__init__
            for j in reversed(range(i)):
                if modules[j] is not None:
                    break
            else:
                # No previous module scope
                continue

            module = modules[j]

        # Only frames relating to the user's package if package_name is provided
        if (package_name is None) or module.__name__.startswith(f"{package_name}.") or (module.__name__ == package_name):
            locals_ = frame_record[0].f_locals
            stack_repr += f'Locals from file "{frame_record.filename}", line {frame_record.lineno}, in {frame_record.function}:\n'
            for var_name in locals_:
                variable = locals_[var_name]
                value_repr = _repr(var_name, variable)
                stack_repr += f"  {var_name} {type(variable)} = "
                stack_repr += value_repr.replace("\n", "\n  ")
                stack_repr += "\n"

            stack_repr += "\n"
            if ("self" in locals_) and hasattr(locals_["self"], "__dict__"):
                stack_repr += "Object dict:\n"
                stack_repr += repr(locals_["self"].__dict__)
                stack_repr += "\n\n"

    return stack_repr


def dump(file_obj: io.TextIOBase, stack: list[inspect.FrameInfo]) -> str:
    """Write the Representation of an Interpreter Stack using a File Object

    Args:
        file_obj (str | io.TextIOBase | io.BufferedIOBase): File object to use for writing.
        stack (list[inspect.FrameInfo]): Stack of frames to dump.
    """
    file_obj.write(dumps(stack))


def dumps(stack: list[inspect.FrameInfo]) -> str:
    """Create a String Representation of an Interpreter Stack

    Externalizes '_stack_dumps' to be accessed by the user.

    Args:
        stack (list[inspect.FrameInfo]): Stack of frames to represent.

    Returns:
        str: Representation of the stack.
    """
    return _stack_dumps(stack, package_name=None)


def _dump(
    stack: list[inspect.FrameInfo],
    e: Exception,
    dump_path: str | bytes | os.PathLike,
) -> str:
    """Internal Function to Dump the Representation of the Interpreter Stack and Exception to File

    Args:
        stack (list[inspect.FrameInfo]): Stack of frames to dump.
        e (Exception): Exception that was raised.
        dump_path (str | bytes | os.PathLike | None): Overridden file path to use for the dump.

    Returns:
        str: Path of the resulting dump.
    """
    dump_repr = _stack_dumps(stack, package_name=_global_package_name) + "\n" + _exception_dumps(e)
    user_dump_path = dump_path or _global_dump_path
    if user_dump_path is not None:
        # User-provided path (assigned when user ran configure, or overridden in this method)
        with open(_resolve_path(user_dump_path), mode="a", encoding="utf-8") as wf:
            wf.write(dump_repr)
            return wf.name
    else:
        # Temporary file
        with tempfile.NamedTemporaryFile(
            "w",
            # Fix the prefix if the user forgot to run 'configure'
            prefix=f"{_global_package_name}_stack_and_locals" if _global_package_name is not None else "stack_and_locals",
            delete=False,
        ) as wf:
            wf.write(dump_repr)
            return wf.name


@contextlib.contextmanager
def dump_on_exception(
    dump_path: str | bytes | os.PathLike | None = None,
) -> None:
    """Content Manager to Dump if an Exception is Raised

    Args:
        dump_path (str | bytes | os.PathLike, optional): Override the file path to use for the dump. Defaults to None.

    Writes a representation of the exception and trace stack to file.
    """
    try:
        yield
    except Exception as e:
        trace = inspect.trace()
        if len(trace) > 1:
            name = _dump(trace[1:], e=e, dump_path=dump_path)
            _logger.fatal(_DUMP_MSG.format(name=name))

        raise


def _set_levels(logger: logging.Logger, level: int) -> None:
    logger.setLevel(level)
    for handler in logger.handlers:
        _logger.debug(f"Logger: {logger.name} - Setting log level for {handler.name} to {level}")
        handler.setLevel(level)


def _remove_handlers(logger: logging.Logger) -> None:
    """Remove All Handlers from an Instantiated Logger"""
    for handler in logger.handlers:
        _logger.debug(f"Logger: {logger.name} - Removing handler: {handler.name}")
        logger.removeHandler(handler)


def configure(
    package_name: str,
    *,
    verbosity: int = 0,
    dump_locals: bool = False,
    dump_path: str | bytes | os.PathLike | None = None,
) -> None:
    """Prepare for Logging

    Args:
        package_name (str): Name of the package to dump from the stack.
        verbosity (int, optional): Level of verbosity (0-2) for log messages. Defaults to 0.
        dump_locals (bool, optional): Dump the caller's stack when logging with a level of warning or higher. Defaults to False.
        dump_path (str | bytes | os.PathLike, optional): Custom path to use when dumping with 'dump_on_exception' or when 'dump_locals=True', otherwise use a temporary path if None. Defaults to None.
    """
    global _global_package_name
    _global_package_name = package_name

    global _global_dump_locals
    _global_dump_locals = dump_locals

    if dump_path is not None:
        global _global_dump_path
        _global_dump_path = _resolve_path(dump_path)

    # Get the root logger
    root_logger = logging.getLogger()

    # Set logging levels using verbosity
    if verbosity > 0:
        _set_levels(root_logger, logging.INFO if verbosity == 1 else logging.DEBUG)

    # Remove existing handlers
    _remove_handlers(root_logger)

    # Add a new stream handler
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=_LOG_FMT, datefmt=_DATE_FMT, style="{"))
    root_logger.addHandler(handler)

    # Set logging level for third-party libraries
    logging.getLogger("requests").setLevel(logging.INFO if verbosity <= 1 else logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.INFO if verbosity <= 1 else logging.DEBUG)


def _resolve_path(path: str | bytes | os.PathLike) -> str:
    """Stringify and Resolve Path-Like Objects

    Args:
        path (str | bytes | os.PathLike): Path-like object to resolve.

    Returns:
        str: Resolved path-like object.
    """
    if isinstance(path, bytes):
        path = path.decode("utf-8")
    elif not isinstance(path, str):
        try:
            path = path.__fspath__()
        except AttributeError:
            raise TypeError(f"Object is not path-like: {path!r}")

    # Expand "~" and "~user" constructions
    path = os.path.expanduser(path)

    # Make absolute if not already
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    return path
