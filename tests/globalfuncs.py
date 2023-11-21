from contextlib import redirect_stdout
from typing import Any, Callable
from os import path, remove, walk
from shutil import rmtree

from .config import TMPDIR


def empty_dir(directory: str):
    "Empty a directory"
    for root, dirs, files in walk(directory):
        for f in files:
            remove(path.join(root, f))
        for d in dirs:
            rmtree(path.join(root, d))


def quiet(func: Callable[..., Any]) -> Callable[..., Any]:
    "A simple decorator function that supresses stdout"
    def wrapper(*args: Any, **kwargs: Any):
        with redirect_stdout(None):
            result = func(*args, **kwargs)
        return result
    return wrapper


def cleanup(func: Callable[..., Any]) -> Callable[..., Any]:
    "A function that removes the temp directory after completion"
    def wrapper(*args: Any, **kwargs: Any):
        func(*args, **kwargs)
        empty_dir(TMPDIR)
    return wrapper
