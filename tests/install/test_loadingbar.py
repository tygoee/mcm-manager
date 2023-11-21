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

import unittest
from ..globalfuncs import quiet

from typing import Iterator
from src.install.loadingbar import loadingbar


class Loadingbar(unittest.TestCase):
    @quiet
    def test_bar(self):
        # Iterating
        abc_list = ['a', 'b', 'c']
        for idx, item in enumerate(loadingbar(abc_list)):
            self.assertEqual(item, abc_list[idx])

        # Using next() and unit='B'
        bar_1 = loadingbar(abc_list, unit='B')
        self.assertEqual(next(bar_1), 'a')

        self.assertEqual(bar_1.iterator, abc_list)
        self.assertIsInstance(bar_1.iterable, Iterator)
        self.assertEqual(bar_1.iterator_len, len(abc_list))

        try:
            bar_1.total
        except AttributeError:
            pass
        else:
            self.fail("bar_1.total != undefined")

        # Refreshing the bar
        bar_1.refresh()

        # Using with-as and a description
        with loadingbar(abc_list, show_desc=True, desc='Test description 1') as bar:
            bar.set_desc("Test description 2")
            self.assertEqual(bar.desc, "Test description 2")

        # Updating with .update() and using total=int
        bar_2: loadingbar[int] = loadingbar(total=100)
        bar_2.update(50)
        self.assertEqual(bar_2.idx, 50)

        self.assertEqual(bar_2.iterator, None)
        self.assertEqual(bar_2.iterable, None)
        self.assertEqual(bar_2.total, 100)

        try:
            bar_2.iterator_len
        except AttributeError:
            pass
        else:
            self.fail("bar_2.iterator_len != undefined")

        # Using both iterator and total
        bar_3 = loadingbar(abc_list, total=20)
        bar_3.update(10)
        self.assertEqual(bar_3.idx, 10)

        self.assertEqual(bar_3.iterator, abc_list)
        self.assertIsInstance(bar_3.iterable, Iterator)
        self.assertEqual(bar_3.total, 20)
        self.assertEqual(bar_3.iterator_len, len(abc_list))
