from os import get_terminal_size
from typing import Collection, Generic, Literal, TypeVar, Optional, Type
from types import TracebackType
from install.filesize import size, traditional

T = TypeVar("T")


class loadingbar(Generic[T]):
    def __init__(
        self, iterator: Collection[T] | None = None, /, *,
        total: int = 0,
        unit: Literal['it', 'B'] = 'it',
        bar_length: int | None = None,
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

        # Define class variables
        self._iter_type: Literal['iter', 'total', 'both']

        if iterator is not None and total == 0:
            self._iter_type = 'iter'
            self.iterator = iterator
            self.iterable = iter(iterator)
            self.iterator_len = len(iterator)
        elif iterator is None and total != 0:
            self._iter_type = 'total'
            self.iterator = None
            self.iterable = None
            self.total = total
        elif iterator is not None and total != 0:
            self._iter_type = 'both'
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
            if i == '{':
                in_brackets = True
            if i == '}':
                in_brackets = False
                continue
            if not in_brackets:
                self.formatting_length += 1

        # Assign or correct bar_length
        self.max_terminal_width = get_terminal_size().columns

        if bar_length == None:
            self.bar_length = self.max_terminal_width
        elif bar_length >= self.max_terminal_width:
            self.bar_length = self.max_terminal_width
        else:
            self.bar_length = bar_length

    def __iter__(self) -> "loadingbar[T]":
        "Method that allows iterators"

        return self

    def __next__(self) -> T:
        "Go to the next iteration"

        # Update the item and idx
        if self.iterable is not None:
            self.item = next(self.iterable)
            self.idx += 1
        elif self.idx < self.total:  # 'total'
            self.idx += 1
        else:
            raise StopIteration

        # Refresh the loading bar
        self.refresh()

        # Return the item
        if self.iterator is not None:  # 'both' or 'iter'
            return self.item
        else:
            return self.idx  # type: ignore

    def __enter__(self) -> "loadingbar[T]":
        "Allow a with-as statement"

        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> bool:
        "Allow a with-as statement"

        return False  # No errors

    def refresh(self) -> None:
        "Refresh the loading bar, called automatically"

        # Calculate progress
        if self._iter_type in ('both', 'total'):
            percent = round(self.idx / self.total * 100, 0)
        else:
            percent = round(self.idx / self.iterator_len * 100, 0)

        if percent >= 100:
            percent = 100

        # Define the current and total
        if self.unit == 'it':
            current = str(self.idx)
            total = str(self.total if self._iter_type in (
                'both', 'total') else self.iterator_len)
        else:
            current = size(self.idx, traditional)
            total = size(self.total if self._iter_type in (
                'both', 'total') else self.iterator_len, traditional)

        # Define the text length
        text_length = self.formatting_length + \
            len(self.title + current + total) + 4

        block = int(round((self.bar_length - text_length) / 100 * percent))

        # Print the loading bar
        start = '\033[F\r' if self.show_desc else '\r'

        if self.show_desc and self._new_desc:
            end = '\n\033[K' + self.desc
        elif self.show_desc:
            end = '\n' + self.desc
        else:
            end = ''

        print(start + self.bar_format.format(
            title=self.title,
            percentage=percent,
            bar='#' * block + ' ' * ((self.bar_length - text_length) - block),
            current=current,
            total=total
        ), end=end)

        # Clear the loading bar at the end
        if self.idx == (self.total if self._iter_type in (
                'both', 'total') else self.iterator_len):
            if self.disappear and self.show_desc:
                print('\r\033[K\033[F\r\033[K', end='')
            elif self.disappear:
                print('\r\033[K', end='')
            elif not self.show_desc:
                print(end='\n')

    def update(self, amount: int) -> None:
        "Add 'n' amount of iterations to the loading bar"
        if self._iter_type == 'iter':
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

    def set_desc(self, description: str):
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
