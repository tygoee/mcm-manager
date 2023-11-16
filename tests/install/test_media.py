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
from ..vars import quiet, empty_dir, current_dir, install_dir

from src.install.media import prepare, download_files
from os import path

unittest.TestLoader.sortTestMethodsUsing = None  # type: ignore
manifest_file = path.join(current_dir, 'assets', 'manifest.json')


class Install(unittest.TestCase):
    def test_media(self):
        self._test_prepare()
        self._test_download()

    @quiet
    def _test_prepare(self):
        manifest = prepare.load_manifest(manifest_file)

        empty_dir(install_dir)
        self.total_size_client = prepare(install_dir, 'client', manifest)

        empty_dir(install_dir)
        self.total_size_server = prepare(install_dir, 'server', manifest)

    @quiet
    def _test_download(self):
        manifest = prepare.load_manifest(manifest_file)

        empty_dir(install_dir)
        download_files(self.total_size_client,
                       install_dir, 'client', manifest)

        empty_dir(install_dir)
        download_files(self.total_size_server,
                       install_dir, 'server', manifest)

    def tearDown(self):
        empty_dir(install_dir)
