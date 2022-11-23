# Yogger

[Yogger](https://github.com/yaphott/yogger) aims to provide an ideal logging setup with utilities to dump the stack and local variables.

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
    # or
    # yogger.configure("my_package")
```

## Support for dumping stack and locals

Use the `dump_on_exception` **context manager**:

```python
with yogger.dump_on_exception():
    raise SomeException
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

To quickly view the contents run the bash command from the dump message:

> Example here is from the log message above.

```Bash
cat '/tmp/my_package_stack_and_locals_hp0ngc90'
```

To handle without using the context manager, something like this would also suffice:

```python
import inspect
```

```python
try:
    ...
except Exception as e:
    trace = inspect.trace()
    if len(trace) > 1:
        logfile_path = yogger.dump_stack_and_locals(trace[1:], e=e)
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

| Parameters              |                                                                                    |
| :---------------------- | :--------------------------------------------------------------------------------- |
| **package_name**_(str)_ | Name of the package to dump from trace stack.                                      |
| **verbosity**_(int)_    | Level of verbosity (0-2).                                                          |
| **dump_locals**_(bool)_ | Dump locals to the logfile (in addition to stack) when log_level>=logging.WARNING. |
| **persist_log**_(bool)_ | Create the logfile in the current working directory instead of "/tmp".             |

### yogger.dump_on_exception

Context manager that dumps the stack and locals to a file if an exception is raised.

| Function Signature  |
| :------------------ |
| dump_on_exception() |

| Parameters |
| :--------- |
| Empty      |

### yogger.dump_stack_and_locals

Dump the stack and locals to a file.

| Function Signature                                          |
| :---------------------------------------------------------- |
| dump_stack_and_locals(trace, \*, e=None, logfile_path=None) |

| Parameters                           |                                 |
| :----------------------------------- | :------------------------------ |
| **trace**_(list[inspect.FrameInfo])_ | Trace to dump                   |
| **e**_(Exception)_                   | Exception that was raised.      |
| **logfile_path**_(str)_              | Custom path to use for logfile. |
