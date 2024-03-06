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

from os import path


class maven_parse:
    def __init__(self, arg: str) -> None:
        """
        Parse java maven coords to a folder and file or to an url.

        Example:
        ```txt
        de.oceanlabs.mcp:mcp_config:1.20.1-20230612.114412@zip
        - folder: de/oceanlabs/mcp/mcp_config/1.20.1-20230612.114412/
        - file: mcp_config-1.20.1-20230612.114412.zip
        ```

        You can get a file path using `.to_file()`
        or an url using `.to_url()`

        To directly access the parsed result,
        use the variable `.parsed`
        """

        self.parsed = self._parse(arg)

    def _parse(self, arg: str) -> tuple[str, str]:
        # Split the file extension
        if '@' in arg:
            arg, ext = arg.split('@', 1)
        else:
            ext = 'jar'

        # Until the third colon, replace
        # ':' with '/'. Until the
        # first, also replace '.' with it
        colons = 0
        folder = ''
        for char in arg:
            if colons == 3:
                break
            if char == ':':
                colons += 1
                char = '/'
            elif char == '.' and colons == 0:
                char = '/'
            folder += char

        if not folder[-1] == '/':
            folder += '/'

        # Select everything from the first
        # colon and replace ':' with '-'
        file = ''
        for char in arg[arg.find(':')+1:]:
            if char == ':':
                char = '-'
            file += char

        # Add the file extension
        file += '.' + ext

        return folder, file

    def to_file(self, *paths: str) -> str:
        """
        Create a file path from the maven coord. This calls
        a `path.join()` with all paths plus `self.parsed`
        """

        parsed = (self.parsed[0].replace('/', path.sep), self.parsed[1])

        return path.join(*paths, *parsed)

    def to_url(self, base: str) -> str:
        """Create a url from the maven coord"""
        if not base[-1] == '/':
            base += '/'

        return ''.join((base, *self.parsed))
