# MCM-Manager: Minecraft Modpack Manager
# Copyright (C) 2023  Tygo Everts
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from os import get_terminal_size
from typing import (
    Collection, Generic, Literal, TypeVar,
    Optional, overload, TYPE_CHECKING
)

if TYPE_CHECKING:
    from types import TracebackType

from .filesize import size, traditional

_T = TypeVar("_T")


class loadingbar(Generic[_T]):
    @overload
    def __init__(
        # total
        self, iterator: Collection[_T], /, *,
        unit: Literal['it', 'B'] = 'it',
        bar_length: Optional[int] = None,
        bar_format: str = "{title} {percentage:3.0f}% [{bar}] {current}/{total}",
        title: str = '',
        show_desc: bool = False,
        desc: str = '',
        disappear: bool = False,
    ) -> None: ...

    @overload
    def __init__(
        # total
        self, /, *,
        total: _T,
        unit: Literal['it', 'B'] = 'it',
        bar_length: Optional[int] = None,
        bar_format: str = "{title} {percentage:3.0f}% [{bar}] {current}/{total}",
        title: str = '',
        show_desc: bool = False,
        desc: str = '',
        disappear: bool = False,
    ) -> None: ...

    @overload
    def __init__(
        # both
        self, iterator: Optional[Collection[_T]] = None, /, *,
        total: int = 0,
        unit: Literal['it', 'B'] = 'it',
        bar_length: Optional[int] = None,
        bar_format: str = "{title} {percentage:3.0f}% [{bar}] {current}/{total}",
        title: str = '',
        show_desc: bool = False,
        desc: str = '',
        disappear: bool = False,
    ) -> None: ...

    def __init__(
        self, iterator: Optional[Collection[_T]] = None, /, *,
        total: int | _T = 0,
        unit: Literal['it', 'B'] = 'it',
        bar_length: Optional[int] = None,
        bar_format: str = "{title} {percentage:3.0f}% [{bar}] {current}/{total}",
        title: str = '',
        show_desc: bool = False,
        desc: str = '',
        disappear: bool = False,
    ) -> None:
        """
        Displays a simple progress bar. Example usage:

        ```python
        my_list = list(range(10))
        for i in bar(my_list)
            do_something()
        ```

        :param iterator: The iterator used by the for loop
        :param total: It's possible to use total=n instead of range()
        :param unit: The unit displayed, `it` = iterations, `B` = bytes
        :param bar_length: The bar length (default: terminal width)
        :param bar_format: The format the loading bar is displayed in
        :param title: The title on the left side of the loading bar
        :param show_desc: Show the description
        :param disappear: If you want the bar to disappear
        """

        if iterator is not None and total == 0:
            # iter
            self.iterator = iterator
            self.iterable = iter(iterator)
            self.iterator_len = len(iterator)
        elif iterator is None and total != 0:
            # total
            self.iterator = None
            self.iterable = None
            self.total = total
        elif iterator is not None and total != 0:
            # both
            self.iterator = iterator
            self.iterable = iter(iterator)
            self.iterator_len = len(iterator)
            self.total = total

        self.idx = 0

        self.unit: Literal['it', 'B'] = unit
        self.bar_format = bar_format
        self.title = title
        self.show_desc = show_desc
        self.desc = desc
        self._new_desc = True
        self.disappear = disappear

        # Get the length of 'formatting'
        self.formatting_length = 0
        in_brackets = False
        for i in bar_format:
            match i:
                case '{':
                    in_brackets = True
                case '}':
                    in_brackets = False
                    continue
                case _: pass

            if not in_brackets:
                self.formatting_length += 1

        # Assign or correct bar_length
        try:
            self.max_terminal_width = get_terminal_size().columns
        except OSError:
            self.max_terminal_width = 80

        if bar_length is None:
            self.bar_length = self.max_terminal_width
        elif bar_length >= self.max_terminal_width:
            self.bar_length = self.max_terminal_width
        else:
            self.bar_length = bar_length

    def __iter__(self) -> "loadingbar[_T]":
        "Method that allows iterators"

        return self

    def __next__(self) -> _T:
        "Go to the next iteration"

        # Update the item and idx
        if self.iterable is not None:
            self.item = next(self.iterable)
            self.idx += 1
        else:
            if TYPE_CHECKING and not isinstance(self.total, int):
                raise TypeError

            if self.idx < self.total:  # total
                self.idx += 1
            else:
                raise StopIteration

        # Refresh the loading bar
        self.refresh()

        # Return the item
        if self.iterator is not None:  # both or iter
            return self.item
        else:
            return self.idx  # type: ignore

    def __enter__(self) -> "loadingbar[_T]":
        "Allow a with-as statement"

        return self

    def __exit__(self, exc_type: Optional[type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional['TracebackType']) -> bool:
        "Allow a with-as statement"

        return False  # No errors

    def refresh(self) -> None:
        "Refresh the loading bar, called automatically"

        # Calculate progress
        if hasattr(self, 'total'):  # both, total
            if TYPE_CHECKING and not isinstance(self.total, int):
                raise TypeError

            percent = round(self.idx / self.total * 100, 0)
        else:
            percent = round(self.idx / self.iterator_len * 100, 0)

        if percent >= 100:
            percent = 100

        # Define the current and total
        if self.unit == 'it':
            current = str(self.idx)
            total = str(self.total if hasattr(
                self, 'total') else self.iterator_len)
        else:
            current = size(self.idx, traditional)
            arg = self.total if hasattr(self, 'total') else self.iterator_len

            if TYPE_CHECKING and not isinstance(arg, int):
                raise TypeError

            total = size(arg, traditional)

        # Define the text length
        text_length = self.formatting_length + \
            len(self.title + current + total) + 4

        block = int(round((self.bar_length - text_length) / 100 * percent))

        # Print the loading bar
        start = '\033[F\r' if self.show_desc else '\r'

        end = (
            '\n\033[K' + self.desc if self.show_desc and self._new_desc
            else '\n' + self.desc if self.show_desc else ''
        )

        print(start + self.bar_format.format(
            title=self.title,
            percentage=percent,
            bar='#' * block + ' ' * ((self.bar_length - text_length) - block),
            current=current,
            total=total
        ), end=end)

        # Clear the loading bar at the end
        if self.idx == (self.total if hasattr(self, 'total') else self.iterator_len):
            if self.disappear and self.show_desc:
                print('\r\033[K\033[F\r\033[K', end='')
            elif self.disappear:
                print('\r\033[K', end='')
            elif not self.show_desc:
                print(end='\n')

    def update(self, amount: int) -> None:
        "Add 'n' amount of iterations to the loading bar"
        if not hasattr(self, 'total'):
            i = 0

            # Call next(self) while less than amount
            while i < amount:
                try:
                    next(self)
                except StopIteration:
                    break

                i += 1
        else:
            self.idx += amount
            self.refresh()

    def set_desc(self, description: str) -> None:
        "Set the description"

        # Cut off the description if it's longer than the terminal width
        if len(description) > self.max_terminal_width:
            description = description[:self.max_terminal_width]

        # Set the description
        self._new_desc = True
        self.desc = description

        # Refresh the loading bar
        self.refresh()
        self._new_desc = False
