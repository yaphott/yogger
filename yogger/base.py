from typing import Any, Optional

import os
import sys
import logging
import collections
import contextlib
import dataclasses
import inspect

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

import tempfile

_logger = logging

_global_package_name = None
_global_dump_locals = False
_global_persist_log = False

# NOTE: Support for colors will be added to Windows later.
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

        if _global_dump_locals:
            stack = inspect.stack()
            if len(stack) > 2:
                name = dump_stack_and_locals(stack[2:][::-1])
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
    # Currently, the user is allowed to run install multiple times
    # if check_installed():
    #     raise RuntimeError("Logging is already using Yogger class")

    # Change to use Yogger class
    logging.setLoggerClass(Yogger)

    global _logger
    _logger = logging.getLogger(__name__)


def _requests_request_repr(
    name: str,
    request: Request,
) -> str:
    """Representation of a requests.Request Object

    Args:
        name (str): Name of the Requests response.
        request (requests.Request): Request object, prepared by the Requests module.

    Returns:
        str: Formatted representation of a requests.Request object.
    """
    msg = ""
    msg += f"{name} = {request!r}"
    msg += f"\n  {name}.method = {request.method}"
    msg += f"\n  {name}.url = {request.url}"
    msg += f"\n  {name}.headers = \\"
    for field in request.headers:
        msg += f'\n    {field} = {_repr("_", request.headers[field])}'

    for attr in ("body", "params", "data"):
        if hasattr(request, attr) and getattr(request, attr):
            msg += f"\n  {name}.{attr} = "
            msg += _repr("_", getattr(request, attr)).replace("\n", "\n  ")

    return msg


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
        with_history (bool): Include the request redirect history in the representation. Defaults to True.

    Returns:
        str: Formatted representation of a requests.Response object.
    """
    msg = ""
    msg += f"{name} = {response!r}"
    msg += f"\n  {name}.url = {response.url}"
    msg += f"\n  {name}.request = "
    msg += _repr("_", response.request).replace("\n", "\n  ")
    if with_history and response.history:
        msg += f"\n  {name}.history = ["
        for prev_resp in response.history:
            msg += "\n    "
            msg += _requests_response_repr("_", prev_resp, with_history=False).replace("\n", "\n    ")

        msg += "\n  ]"

    msg += f"\n  {name}.status_code = {response.status_code}"
    msg += f"\n  {name}.headers = \\"
    for field in response.headers:
        msg += f'\n    {field} = {_repr("_", response.headers[field])}'

    msg += f'\n  {name}.content = {_repr("_", response.content)}'
    return msg


def _requests_exception_repr(
    name: str,
    e: RequestException,
) -> str:
    """Formatted Representation of a requests.exceptions.RequestException

    Args:
        name (str): Name of the Requests Exception.
        e (requests.exceptions.RequestException): Requests exception to represent.

    Returns:
        str: Formatted representation of a Requests exception.
    """
    msg = ""
    msg += f"{name} = {e!r}"
    msg += "\n  " + _repr(f"{name}.request", e.request).replace("\n", "\n  ")
    msg += "\n  " + _repr(f"{name}.response", e.response).replace("\n", "\n  ")
    return msg


def _repr(name: str, value: Any) -> str:
    """Formatted Representation of a Variable Name and Value

    Args:
        name (str): Name of the variable to represent.
        value (Any): Value to represent.

    Returns:
        str: Formatted representation of a value.
    """
    if _has_requests_package:
        if type(value) is Response:
            return _requests_response_repr(name, value)

        if type(value) in (PreparedRequest, Request):
            return _requests_request_repr(name, value)

        if isinstance(value, RequestException):
            return _requests_exception_repr(name, value)

    if isinstance(value, dict):
        return f"{name} = <{type(value).__module__}.{type(value).__name__}>\n  " + "\n  ".join(_repr(f"{name}[{k!r}]", v).replace("\n", "\n  ") for k, v in value.items())

    if isinstance(value, (list, tuple, collections.deque)) and not all(isinstance(v, (int, str)) for v in value):
        return f"{name} = <{type(value).__module__}.{type(value).__name__}>\n  " + "\n  ".join(_repr(f"{name}[{i}]", v).replace("\n", "\n  ") for i, v in enumerate(value))

    if dataclasses.is_dataclass(value):
        return f"{name} = <{type(value).__module__}.{type(value).__name__}>\n  " + "\n  ".join(
            _repr(f"{name}.{f.name}", f.name) + " = " + _repr(f"{name}.{f.name}", getattr(value, f.name)).replace("\n", "\n  ") for f in dataclasses.fields(value)
        )

    value_repr = f"{name} = {value!r}"
    if "\n" in value_repr:
        return "\\\n  " + value_repr.replace("\n", "\n  ")

    return value_repr


def dump_stack_and_locals(
    trace: list[inspect.FrameInfo],
    *,
    e: Optional[Exception] = None,
    logfile_path: Optional[str] = None,
) -> str:
    """Dump the Stack and Locals to a File

    Args:
        trace (list[inspect.FrameInfo]): Trace to dump.
        e (Exception, optional): Exception that was raised. Defaults to None.
        logfile_path (str, optional): Custom path to use for logfile. Defaults to None.

    Returns:
        str: Path of the resulting logfile.
    """
    # Currently, the user is allowed to run install multiple times.
    # _ensure_installed()

    # Currently, the user is allowed to run configure multiple times.
    # _ensure_configured()

    base_filename = f"{_global_package_name}_stack_and_locals"
    if logfile_path is not None:
        # User-provided file path
        f = open(
            os.path.abspath(logfile_path) if not os.path.isabs(logfile_path) else logfile_path,
            # Overwrite if not persisting log
            mode="a" if _global_persist_log else "w",
            encoding="utf-8",
        )
    else:
        if _global_persist_log:
            # Current working directory
            f = open(
                os.path.join(os.getcwd(), f"{base_filename}.log"),
                mode="a",
                encoding="utf-8",
            )
        else:
            # Temporary directory
            f = tempfile.NamedTemporaryFile("w", prefix=f"{base_filename}_", delete=False)

    try:
        # Record the cause exception
        if e is not None:
            f.write("Exception:\n")
            f.write(f"  {type(e).__module__}.{type(e).__name__}: {e!s}\n")
            f.write(f"  args: {e.args!r}\n")
            f.write("\n")

        # Record the code contexts
        f.write("Stack:\n")
        for frame_record in trace:
            f.write(f'  File "{frame_record.filename}", line {frame_record.lineno}, in {frame_record.function}\n')
            if frame_record.code_context is not None:
                for line in frame_record.code_context:
                    f.write(f"    {line.strip()}\n")

        f.write("\n")

        # Record representations of locals
        modules = [inspect.getmodule(frame_record[0]) for frame_record in trace]
        for i, (module, frame_record) in enumerate(zip(modules, trace)):
            if module is None:
                # Moduleless frame, e.g. dataclass.__init__
                for j in reversed(range(i)):
                    if modules[j] is not None:
                        break
                else:
                    # No previous module scope
                    continue

                module = modules[j]

            # Only dump locals
            if module.__name__.startswith(f"{_global_package_name}.") or (module.__name__ == _global_package_name):
                locals_ = frame_record[0].f_locals
                f.write(f'Locals from file "{frame_record.filename}", line {frame_record.lineno}, in {frame_record.function}:\n')
                for var_name in locals_:
                    variable = locals_[var_name]
                    var_repr = _repr(var_name, variable)
                    f.write(f"  {var_name} {type(variable)} = ")
                    f.write(var_repr.replace("\n", "\n  "))
                    f.write("\n")

                f.write("\n")
                if ("self" in locals_) and hasattr(locals_["self"], "__dict__"):
                    f.write("Object dict:\n")
                    f.write(repr(locals_["self"].__dict__))
                    f.write("\n\n")

        # Location of log file
        name = f.name
    finally:
        f.close()

    return name


@contextlib.contextmanager
def dump_on_exception() -> None:
    """Content Manager that Dumps if an Exception is Raised"""
    try:
        yield
    except Exception as e:
        trace = inspect.trace()
        if len(trace) > 1:
            name = dump_stack_and_locals(trace[1:], e=e)
            _logger.fatal(_DUMP_MSG.format(name=name))

        raise


def _set_levels(root_logger: logging.Logger, level: int) -> None:
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        _logger.debug(f"Setting log level to {level} for handler: {handler.name}")
        handler.setLevel(level)


def _remove_handlers(root_logger: logging.Logger) -> None:
    for handler in root_logger.handlers:
        _logger.debug(f"Removing handler: {handler.name}")
        root_logger.removeHandler(handler)


def configure(
    package_name: str,
    *,
    verbosity: int = 0,
    dump_locals: bool = False,
    persist_log: bool = False,
) -> None:
    """Prepare for Logging

    Args:
        package_name (str): Name of the package to dump from trace stack.
        verbosity (int, optional): Level of verbosity (0-2 using current implementation). Defaults to 0.
        dump_locals (bool, optional): Dump local variables when logging level is warning or higher. Defaults to False.
        persist_log (bool, optional): Create the logfile in the current working directory instead of "/tmp". Defaults to False.
    """
    # Currently, the user is allowed to run configure multiple times.
    # if not check_configured():
    #     ...

    # Currently, the user is allowed to run install multiple times.
    # _ensure_installed()

    global _global_package_name
    _global_package_name = package_name

    global _global_dump_locals
    _global_dump_locals = dump_locals

    global _global_persist_log
    _global_persist_log = persist_log

    root_logger = logging.getLogger()

    # Set logging levels using verbosity
    if verbosity > 0:
        _set_levels(root_logger, logging.INFO if verbosity == 1 else logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        fmt="[ {asctime}.{msecs:04.0f}  \33[1m{levelname}\33[0m  {name} ]  {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )

    # Remove existing handlers
    _remove_handlers(root_logger)

    # Add a new stream handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Set logging level for third-party libraries
    logging.getLogger("requests").setLevel(logging.INFO if verbosity <= 1 else logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.INFO if verbosity <= 1 else logging.DEBUG)
