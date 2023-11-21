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
from ..config import CURDIR, INSTDIR
from ..globalfuncs import cleanup, quiet
from .setup import setup_dirs

from src.install.media import prepare, download_files
from os import path

manifest_file = path.join(CURDIR, 'assets', 'manifest.json')


class Install(unittest.TestCase):
    # These tests need some serious improvement
    def test_media(self):
        # Create the manifest
        self.manifest = prepare.load_manifest(manifest_file)

        # Run all sub tests in order
        self._test_prepare_client()
        self._test_prepare_server()
        self._test_download_client()
        self._test_download_server()

    @quiet
    @cleanup
    def _test_prepare_client(self):
        setup_dirs()
        self.total_size_client = prepare(
            INSTDIR, 'client', self.manifest).total_size

        self.assertIsInstance(self.total_size_client, int)

    @quiet
    @cleanup
    def _test_prepare_server(self):
        setup_dirs()
        self.total_size_server = prepare(
            INSTDIR, 'server', self.manifest).total_size

        self.assertIsInstance(self.total_size_server, int)

    @quiet
    @cleanup
    def _test_download_client(self):
        setup_dirs()
        download_files(self.total_size_client,
                       INSTDIR, 'client', self.manifest)

    @quiet
    @cleanup
    def _test_download_server(self):
        setup_dirs()
        download_files(self.total_size_server,
                       INSTDIR, 'server', self.manifest)
