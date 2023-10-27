# This program is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this
# program. If not, see <https://www.gnu.org/licenses/>.

import unittest
from ..vars import quiet, empty_dir, install_dir

from src.install.modloaders import forge, fabric


class Install(unittest.TestCase):
    @quiet
    def test_forge_client(self):
        empty_dir(install_dir)
        forge('1.20.1', '47.1.0', 'client', install_dir)

    @quiet
    def test_forge_server(self):
        empty_dir(install_dir)
        forge('1.20.1', '47.1.0', 'server', install_dir)


if False:  # Tests of unfinished features
    @quiet
    def test_fabric_client(self):
        empty_dir(install_dir)
        fabric('1.20.1', '0.14.22', 'client', install_dir)

    @quiet
    def test_fabric_server(self):
        empty_dir(install_dir)
        fabric('1.20.1', '0.14.22', 'server', install_dir)
