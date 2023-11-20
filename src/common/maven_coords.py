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


def maven_parse(arg: str) -> tuple[str, str]:
    """
    Parse java maven coords to a folder and a file.

    Example:
    ```txt
    de.oceanlabs.mcp:mcp_config:1.20.1-20230612.114412@zip
    - folder: de/oceanlabs/mcp/mcp_config/1.20.1-20230612.114412/
    - file: mcp_config-1.20.1-20230612.114412.zip
    ```
    maven_"""

    # Split the file extension
    if '@' in arg:
        arg, ext = arg.split('@', 1)
    else:
        ext = 'jar'

    # Until the third colon, replace
    # ':' with path.sep. Until the
    # first, also replace '.' with it
    colons = 0
    folder = ''
    for char in arg:
        if colons == 3:
            folder += path.sep
            break
        if char == ':':
            colons += 1
            char = path.sep
        elif char == '.' and colons == 0:
            char = path.sep
        folder += char

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


def maven_to_file(*paths: str) -> str:
    """
    Create a file path from a maven coord.
    The last argument should be `arg`
    """
    return path.join(*paths[:-1], *maven_parse(paths[-1]))


def maven_to_url(base: str, arg: str) -> str:
    """Create a url from a maven coord"""
    if not base[-1] == '/':
        base += '/'

    return ''.join((base, *maven_parse(arg)))
