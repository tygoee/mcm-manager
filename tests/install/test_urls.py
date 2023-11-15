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
from src.install.urls import media_url, forge
from src.install._types import Media


class Install(unittest.TestCase):
    def test_urls(self):
        # Define different media types
        cf_media: Media = {
            "type": "cf",
            "slug": "worldedit",
            "name": "worldedit-mod-7.2.15.jar",
            "id": 4586218,
            "sides": [
                "server"
            ]
        }

        pm_media: Media = {
            "type": "pm",
            "slug": "1-13-1-16-unique-spawn-eggs",
            "name": "unique-spawn-eggs-v1-5.zip",
            "media": "texture",
            "sides": [
                "client",
                "server"
            ]
        }

        mr_media: Media = {
            "type": "mr",
            "slug": "sodium",
            "name": "sodium-fabric-mc1.20.1-0.5.1.jar",
            "id": "AANobbMIOkwCNtFH",
            "sides": [
                "client"
            ]
        }

        url_media: Media = {
            "type": "url",
            "slug": "essential",
            "name": "Essential-fabric_1-20-1.jar",
            "url": "https://cdn.essential.gg/mods/60ecf53d6b26c76a26d49e5b/" +
                   "649c45fb8b045520b2c1c8b2/Essential-fabric_1-20-1.jar",
            "info": {
                "title": "Essential",
                "icon": "https://static.essential.gg/icon/256x256.png",
                "description": "Essential is a quality of life mod that boosts Minecraft Java to the next level."
            },
            "sides": [
                "client",
                "server"
            ]
        }

        # Test if they assert equal
        cases = {
            media_url(cf_media): 'https://mediafilez.forgecdn.net/files/4586/218/worldedit-mod-7.2.15.jar',
            media_url(pm_media): 'https://static.planetminecraft.com/files/resource_media/texture/unique-spawn-eggs-v1-5.zip',
            media_url(mr_media): 'https://cdn-raw.modrinth.com/data/AANobbMI/versions/' +
                                 'OkwCNtFH/sodium-fabric-mc1.20.1-0.5.1.jar',
            media_url(url_media): url_media['url']
        }

        for k, v in cases.items():
            self.assertEqual(k, v)

        # Test the forge urls
        self.assertEqual(
            forge.version_manifest_v2,
            "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        )

        self.assertEqual(
            forge.forge_installer_url('1.20.1', '47.1.0'),
            "https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.1.0/forge-1.20.1-47.1.0-installer.jar"
        )
