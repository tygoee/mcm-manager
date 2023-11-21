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
from ..config import INSTDIR, LAUNDIR
from ..globalfuncs import cleanup, quiet
from .setup import setup_dirs

from src.install.modloaders import forge, fabric


class Modloaders(unittest.TestCase):
    @quiet
    @cleanup
    def test_forge_client(self):
        setup_dirs()
        forge('1.20.1', '47.1.0', 'client', INSTDIR, LAUNDIR)

    @quiet
    @cleanup
    def test_forge_server(self):
        setup_dirs()
        forge('1.20.1', '47.1.0', 'server', INSTDIR)


if False:  # Tests of unfinished features
    @quiet
    @cleanup
    def test_fabric_client(self):
        setup_dirs()
        fabric('1.20.1', '0.14.22', 'client', INSTDIR)

    @quiet
    @cleanup
    def test_fabric_server(self):
        setup_dirs()
        fabric('1.20.1', '0.14.22', 'server', INSTDIR)
