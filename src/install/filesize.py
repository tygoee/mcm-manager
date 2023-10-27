# This is a copy from `hurry.filesize` but with type annotations
# Source: https://pypi.org/project/hurry.filesize/

from ._types import SizeSystem

traditional: SizeSystem = [
    (1024 ** 5, 'P'),
    (1024 ** 4, 'T'),
    (1024 ** 3, 'G'),
    (1024 ** 2, 'M'),
    (1024 ** 1, 'K'),
    (1024 ** 0, 'B'),
]

alternative: SizeSystem = [
    (1024 ** 5, ' PB'),
    (1024 ** 4, ' TB'),
    (1024 ** 3, ' GB'),
    (1024 ** 2, ' MB'),
    (1024 ** 1, ' KB'),
    (1024 ** 0, (' byte', ' bytes')),
]

verbose: SizeSystem = [
    (1024 ** 5, (' petabyte', ' petabytes')),
    (1024 ** 4, (' terabyte', ' terabytes')),
    (1024 ** 3, (' gigabyte', ' gigabytes')),
    (1024 ** 2, (' megabyte', ' megabytes')),
    (1024 ** 1, (' kilobyte', ' kilobytes')),
    (1024 ** 0, (' byte', ' bytes')),
]

iec: SizeSystem = [
    (1024 ** 5, 'Pi'),
    (1024 ** 4, 'Ti'),
    (1024 ** 3, 'Gi'),
    (1024 ** 2, 'Mi'),
    (1024 ** 1, 'Ki'),
    (1024 ** 0, ''),
]

si: SizeSystem = [
    (1000 ** 5, 'P'),
    (1000 ** 4, 'T'),
    (1000 ** 3, 'G'),
    (1000 ** 2, 'M'),
    (1000 ** 1, 'K'),
    (1000 ** 0, 'B'),
]


def size(bytes: int, system: SizeSystem) -> str:
    """Human-readable file size."""

    suffix: str | tuple[str, str] = ''
    factor: int = 0
    for factor, suffix in system:
        if bytes >= factor:
            break
    amount = int(bytes/factor)
    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix
