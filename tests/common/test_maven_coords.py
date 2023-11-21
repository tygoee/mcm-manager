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

from src.common.maven_coords import maven_parse


class MavenParse(unittest.TestCase):
    def test_maven_coords(self):
        cases: list[tuple[str, tuple[str, str], str, str]] = [
            (  # With three parts
                'net.fabricmc:fabric-loader:0.14.22', (
                    'net/fabricmc/fabric-loader/0.14.22/',
                    'fabric-loader-0.14.22.jar'
                ),
                'libraries/net/fabricmc/fabric-loader/0.14.22/'
                'fabric-loader-0.14.22.jar',
                'https://example.com/net/fabricmc/fabric-loader'
                '/0.14.22/fabric-loader-0.14.22.jar'
            ),
            (  # With four parts
                'net.minecraft:client:1.20.1-20230612.114412:slim', (
                    'net/minecraft/client/1.20.1-20230612.114412/',
                    'client-1.20.1-20230612.114412-slim.jar'
                ),
                'libraries/net/minecraft/client/1.20.1-20230612.114412/'
                'client-1.20.1-20230612.114412-slim.jar',
                'https://example.com/net/minecraft/client/'
                '1.20.1-20230612.114412/client-1.20.1-20230612.114412-slim.jar'
            ),
            (  # With three parts and a file extension
                'de.oceanlabs.mcp:mcp_config:1.20.1-20230612.114412@zip', (
                    'de/oceanlabs/mcp/mcp_config/1.20.1-20230612.114412/',
                    'mcp_config-1.20.1-20230612.114412.zip'
                ),
                'libraries/de/oceanlabs/mcp/mcp_config/1.20.1-20230612.114412/'
                'mcp_config-1.20.1-20230612.114412.zip',
                'https://example.com/de/oceanlabs/mcp/mcp_config/'
                '1.20.1-20230612.114412/mcp_config-1.20.1-20230612.114412.zip'
            ),
            (  # With four parts and a file extension
                'de.oceanlabs.mcp:mcp_config:1.20.1-20230612.114412:mappings@txt', (
                    'de/oceanlabs/mcp/mcp_config/1.20.1-20230612.114412/',
                    'mcp_config-1.20.1-20230612.114412-mappings.txt'
                ),
                'libraries/de/oceanlabs/mcp/mcp_config/1.20.1-20230612.114412/'
                'mcp_config-1.20.1-20230612.114412-mappings.txt',
                'https://example.com/de/oceanlabs/mcp/mcp_config/'
                '1.20.1-20230612.114412/mcp_config-1.20.1-20230612.114412-mappings.txt'
            )
        ]

        for i in cases:
            maven = maven_parse(i[0])
            self.assertEqual(maven.parsed, i[1])
            self.assertEqual(maven.to_file('libraries'), i[2])
            self.assertEqual(maven.to_url('https://example.com'), i[3])
