# Yogger

[Yogger](https://github.com/yaphott/yogger) aims to provide an ideal logging setup with utilities to effectively represent interpreter stacks.

> Supports `requests.Request` and `requests.Response` objects if the **Requests** package is installed.

Example of logger output:

```text
[ 2022-11-17 10:16:09.0918  INFO  my_package.base ]  Something we want to log.
[ 2022-11-17 10:16:09.0918  DEBUG  my_package.base ]  Something we want to log.
[ 2022-11-17 10:16:09.0918  WARNING  my_package.base ]  Something we want to log.
[ 2022-11-17 10:16:09.0918  ERROR  my_package.base ]  Something we want to log.
[ 2022-11-17 10:16:09.0918  CRITICAL  my_package.base ]  Something we want to log.
```

Example of dictionary representation in dump:

```python
example = {
    "user_id": 123456790,
    "profile": {
        "name": "John Doe",
        "birthdate": datetime.date(2000, 1, 1),
        "weight_kg": 86.18,
    },
    "video_ids": [123, 456, 789],
}
```

```text
example = <builtins.dict>
  example['user_id'] = 123456790
  example['profile'] = <builtins.dict>
    example['profile']['name'] = 'John Doe'
    example['profile']['birthdate'] = datetime.date(2000, 1, 1)
    example['profile']['weight_kg'] = 86.18
  example['video_ids'] = [123, 456, 789]
```

Similarly for a dataclass:

```python
@dataclasses.dataclass
class Example:
    user_id: int
    profile: dict[str, str | float | datetime.date]
    video_ids: list[int]
```

```text
example = <my_package.Example>
  example.user_id = 'user_id' = example.user_id = 123456790
  example.profile = 'profile' = example.profile = <builtins.dict>
    example.profile['name'] = 'John Doe'
    example.profile['birthdate'] = datetime.date(2000, 1, 1)
    example.profile['weight_kg'] = 86.18
  example.video_ids = 'video_ids' = example.video_ids = [123, 456, 789]
```

## Requirements:

**Yogger** requires Python 3.9 or higher, is platform independent, and requires no outside dependencies.

## Installing

Most stable version from [**PyPi**](https://pypi.org/project/yogger/):

```bash
pip install yogger
```

Development version from [**GitHub**](https://github.com/yaphott/yogger):

```bash
git clone git+https://github.com/yaphott/yogger.git
cd yogger
pip install .
```

## Usage

Import packages and instantiate a logger:

```python
import logging
import yogger

logger = logging.getLogger(__name__)
```

Install the logger class and configure with your package name:

> Place at the start of the top-level function.

```python
def _cli():
    yogger.install()
    yogger.configure(__name__)
```

### About the `package_name` parameter

The `package_name` parameter gives Yogger an idea of what belongs to your application. This name is used to identify which frames to dump in the stack. So it’s important what you provide there. If you are using a single module, `__name__` is always the correct value. If you are using a package, it’s usually recommended to hardcode the name of your package there.

For example, if your application is defined in "yourapplication/app.py", you should create it with one of the two versions below:

```python
yogger.configure("yourapplication")
```

```python
yogger.configure(__name__.split(".")[0])
```

Why is that? The application will work even with `__name__`, thanks to how resources are looked up. However, it will make debugging more painful. Yogger makes assumptions based on the import name of your application. If the import name is not properly set up, that debugging information may be lost.

## Support for dumping the stack

### Traces and exceptions

Using the `dump_on_exception` **context manager** dumps the exception and trace if an exception is raised:

```python
with yogger.dump_on_exception():
    raise SomeException
```

This is equivalent to running:

```python
import inspect
```

```python
try:
    raise SomeException
except Exception as e:
    trace = inspect.trace()
    if len(trace) > 1:
        logfile_path = yogger.dump(trace[1:], e=e)
```

Example of output:

```text
[ 2022-11-17 10:16:09.0918  CRITICAL  yogger.base ]
Dumped stack and locals to '/tmp/my_package_stack_and_locals_hp0ngc90'

Copy and paste the following to view:
    cat '/tmp/my_package_stack_and_locals_hp0ngc90'

Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
SomeException
```

To quickly view the contents, run the bash command from the log message:

> Example here is from the log message above.

```Bash
cat '/tmp/my_package_stack_and_locals_hp0ngc90'
```

### Stacks

Setting `dump_locals=True` dumps a representation of the caller's stack upon logging with a level of warning or higher.

To manually dump the stack, something like this would suffice:

```python
import inspect
```

```python
stack = inspect.stack()
if len(stack) > 2:
    file_path = yogger.dump(stack[2:][::-1])
```

The log file path may be specified by providing the `logfile_path` keyword argument:

```python
stack = inspect.stack()
if len(stack) > 2:
    yogger.dump(stack[2:][::-1], logfile_path="./example.log")
```

---

## Library

### yogger.install

Function to install the logger class and instantiate the global logger.

| Function Signature |
| :----------------- |
| install()          |

| Parameters |
| :--------- |
| Empty      |

### yogger.configure

Function to prepare for logging.

| Function Signature                                                             |
| :----------------------------------------------------------------------------- |
| configure(package_name, \*, verbosity=0, dump_locals=False, persist_log=False) |

| Parameters              |                                                                         |
| :---------------------- | :---------------------------------------------------------------------- |
| **package_name**_(str)_ | Name of the package to dump from the stack.                             |
| **verbosity**_(int)_    | Level of verbosity (0-2).                                               |
| **dump_locals**_(bool)_ | Dump the caller's stack when logging with a level of warning or higher. |
| **persist_log**_(bool)_ | Create the logfile in the current working directory instead of "/tmp".  |

### yogger.dump_on_exception

Context manager to dump a representation of the exception and trace stack to file if an exception is raised.

| Function Signature  |
| :------------------ |
| dump_on_exception() |

| Parameters |
| :--------- |
| Empty      |

### yogger.dump

Function to dump a representation of an interpreter stack and exception (if provided) to file.

| Function Signature                         |
| :----------------------------------------- |
| dump(stack, \*, e=None, logfile_path=None) |

| Parameters                           |                                 |
| :----------------------------------- | :------------------------------ |
| **stack**_(list[inspect.FrameInfo])_ | Stack to dump                   |
| **e**_(Exception)_                   | Exception that was raised.      |
| **logfile_path**_(str)_              | Custom path to use for logfile. |

### yogger.dumps

Function to create a string representation of an interpreter stack and exception (if provided).

| Function Signature       |
| :----------------------- |
| dumps(stack, \*, e=None) |

| Parameters                           |                            |
| :----------------------------------- | :------------------------- |
| **stack**_(list[inspect.FrameInfo])_ | Stack to represent.        |
| **e**_(Exception)_                   | Exception that was raised. |
