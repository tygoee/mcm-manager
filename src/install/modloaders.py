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

from atexit import register
from json import load, dump
from os import path, getenv, mkdir, makedirs, rename
from shutil import rmtree, copyfile
from subprocess import check_call, DEVNULL
from sys import platform
from typing import TYPE_CHECKING
from urllib import request
from zipfile import ZipFile

if TYPE_CHECKING:
    from http.client import HTTPResponse

from .loadingbar import loadingbar
from .urls import forge as forge_urls

from ..common.maven_coords import maven_parse
from ..apis import fabric_meta, piston_meta

from ..typings import (
    Side, Modloader,
    ForgeLibrary, OSLibrary,
    InstallProfile, Libraries,
    ForgeVersionJson
)

# Define the minecraft directory
_minecraft_dirs = {
    "win32": path.join(getenv('APPDATA', ''), ".minecraft"),
    "linux": path.join(path.expanduser("~"), ".minecraft"),
    "darwin": path.join(path.expanduser("~"), "Library", "Application Support", "minecraft"),
}

# Defaulting to '' is intentional behavior,
# it'll raise an error when trying to write
MINECRAFT_DIR = _minecraft_dirs.get(platform, '')


class forge:
    def __init__(self, mc_version: str,
                 forge_version: str,
                 side: Side = 'client',
                 install_dir: str = MINECRAFT_DIR,
                 launcher_dir: str = MINECRAFT_DIR) -> None:
        """
        Installs a specified forge version

        :param mc_version: The minecraft version, for example `'1.20.1'`
        :param forge_version: The forge version, for example `'47.1.0'`
        :param side: The side; `'client'` or `'server'`
        :param install_dir: The directory minecraft forge gets installed
        :param launcher_dir: The launcher dir (ignored if on server side)
        """

        # Define the class variables
        launcher_dir = install_dir if side == 'server' else launcher_dir

        self.mc_version = mc_version
        self.forge_version = forge_version
        self.side: Side = side
        self.install_dir = install_dir
        self.launcher_dir = launcher_dir

        self.temp_dir = path.join(launcher_dir, '.temp')
        self.minecraft_json = piston_meta.get_minecraft_json(mc_version)
        self.installer = path.join(
            self.temp_dir, f'forge-{mc_version}-{forge_version}-installer.jar')

        if side == 'client':
            self.minecraft_jar = path.join(launcher_dir, 'versions',
                                           mc_version, f"{mc_version}.jar")
        else:
            self.minecraft_jar = path.join(self.temp_dir, f"{mc_version}.jar")

        # Check if java is installed
        try:
            check_call(['java', '--version'], stdout=DEVNULL)
        except FileNotFoundError:
            raise FileNotFoundError(
                "Java was not found in the system's PATH. Please make sure "
                "you have Java installed and it is properly configured."
            )

        # Exit if the launcher hasn't launched once
        if not path.isfile(path.join(launcher_dir, 'launcher_profiles.json')) and side == 'client':
            raise FileNotFoundError(
                "Launch the launcher once before installing forge.")

        # Download the jar files
        self.download_jar_files()

        # Load all the json data
        with ZipFile(self.installer, 'r') as archive:
            # Read the json files in the archive
            with archive.open('install_profile.json') as fp:
                self.install_profile: InstallProfile = load(fp)
            with archive.open('version.json') as fp:
                self.version_json: ForgeVersionJson = load(fp)

            # Define the forge dir
            forge_dir = path.join(
                launcher_dir, 'versions', f"{mc_version}-forge-{forge_version}")

            # Write the json files to the launcher dir
            if not path.isfile(path.join(forge_dir, f"{mc_version}-forge-{forge_version}.json")) and side == 'client':
                if not path.isdir(forge_dir):
                    mkdir(forge_dir)

                archive.extract('version.json', forge_dir)
                rename(path.join(forge_dir, 'version.json'),
                       path.join(forge_dir, f"{mc_version}-forge-{forge_version}.json"))

        # Inject launcher profiles
        if side == 'client':
            with open(path.join(launcher_dir, 'launcher_profiles.json'), 'r') as fp:
                launcher_profiles = load(fp)

            with open(path.join(launcher_dir, 'launcher_profiles.json'), 'w') as fp:
                launcher_profiles['profiles'][f'forge-{mc_version}'] = {
                    "gameDir": install_dir,
                    "icon": self.install_profile['icon'],
                    "lastUsed": "1970-01-02T00:00:00.000Z",
                    "lastVersionId": self.version_json['id'],
                    "name": f"forge {mc_version}",
                    "type": "custom"
                }
                dump(launcher_profiles, fp, indent=2)

        # Install all libraries
        self.install_libraries()

        # Build the processors
        self.build_processors()

    def replace_arg_vars(self, arg: str, data: dict[str, str]) -> str:
        """Replace the java argument variables"""

        # Replace the bracket-enclosed variables
        # in the arg string with **data
        arg = arg.format(**data)

        # Extract when a path ends with '.lzma'
        if arg.endswith('.lzma'):
            with ZipFile(self.installer, 'r') as archive:
                archive.extract(arg[1:], self.temp_dir)
            return path.join(self.temp_dir, path.normpath(arg[1:]))

        # Return arg when it isn't "[something]"
        if arg[0] != '[' and arg[-1] != ']':
            return arg

        # Remove the brackets
        arg = arg[1:-1]

        # Return the full path
        return maven_parse(arg).to_file(self.launcher_dir, 'libraries')

    def download_jar_files(self) -> None:
        """Download the jar files"""

        # Create the temp dir
        if not path.isdir(self.temp_dir):
            mkdir(self.temp_dir)
        else:
            rmtree(self.temp_dir)
            mkdir(self.temp_dir)

        # Delete the temp dir at exit
        register(lambda: rmtree(self.temp_dir) if path.isdir(
            self.temp_dir) else None)

        if self.side == 'client':
            # Make the required directories
            for directory in [
                    path.join(self.launcher_dir, 'versions'),
                    path.join(self.launcher_dir, 'versions', self.mc_version)
            ]:
                if not path.isdir(directory):
                    mkdir(directory)

            # Write the (version).json file
            with open(path.join(self.launcher_dir, 'versions', self.mc_version,
                                f"{self.mc_version}.json"), 'w') as fp:
                dump(self.minecraft_json, fp, indent=2)

        # Define the download urls
        downloads = {
            self.installer: forge_urls.forge_installer_url(self.mc_version, self.forge_version),
            self.minecraft_jar: self.minecraft_json['downloads'][self.side]['url']
        }

        # Download everything
        for fname, url in downloads.items():
            resp: 'HTTPResponse'
            with request.urlopen(url) as resp, open(path.join(fname), 'wb') as mod_file:
                while True:
                    resp_data = resp.read(1024)
                    if not resp_data:
                        break
                    mod_file.write(resp_data)

    def download_library(self, bar: loadingbar[ForgeLibrary | OSLibrary], library: ForgeLibrary) -> None:
        """Download a library"""
        # Define the java os names
        osdict = {
            "windows": "win32",
            "linux": "linux",
            "osx": "darwin"
        }

        # Don't download if it's not for the current os
        if 'action' in library and library['action'] == 'allow' and \
                platform != osdict[library['os']['name']]:
            bar.update(library['size'])
            bar.refresh()
            return

        if 'action' in library and library['action'] == 'disallow' and \
                platform == osdict[library['os']['name']]:
            bar.update(library['size'])
            bar.refresh()
            return

        # Define the library path
        library_path = path.normpath(library['path'])
        full_library_path = path.join(
            self.launcher_dir, 'libraries', library_path)

        # Make the directories to place the files in
        for index, directory in enumerate(
            splitted_path := ['libraries', *library_path.split(path.sep)[:-1]]
        ):
            if not path.isdir(joined_path := path.join(
                    self.launcher_dir, *splitted_path[:index], directory)):
                mkdir(joined_path)

        # If the url is '', copy from the installer
        if library['url'] == '':
            with ZipFile(self.installer) as archive:
                archive.extract(f"maven/{library['path']}", self.temp_dir)
            if not path.isfile(full_library_path):
                rename(path.join(self.temp_dir, 'maven',
                                 library_path), full_library_path)  # Move to the right dir
            return

        # Check if the files don't already exist
        if path.isfile(full_library_path):
            # Just update the bar and return if they exist
            bar.update(library['size'])
            bar.refresh()
            return

        # Download the files
        # TODO: Check the sha1
        with request.urlopen(library['url']) as resp, open(full_library_path, 'wb') as mod_file:
            while True:
                resp_data = resp.read(1024)
                if not resp_data:
                    break
                size = mod_file.write(resp_data)
                bar.update(size)

    def install_libraries(self) -> None:
        """Installs all libraries"""

        # Define the libaries
        self.libraries: Libraries = {}

        # Add all libraries to the libraries dict
        for library in (self.install_profile.get('libraries', []) +
                        self.version_json.get('libraries', []) +
                        self.minecraft_json.get('libraries', [])):

            # Add the library to libraries
            rules = library.get('rules', [])

            self.libraries[library['name']] = library['downloads']['artifact']

            # A bug in the type checker, it worked earlier
            self.libraries[library['name']].update(
                rules[-1] if rules else {})  # type: ignore

        # Define the total size
        total_size = sum([library['size']
                         for library in self.libraries.values()])

        # Download all libraries
        for library in (bar := loadingbar(
            self.libraries.values(),
            unit='B',
            title="Downloading Forge:",
            disappear=True,
            total=total_size,
        )):
            self.download_library(bar, library)

    def build_processors(self) -> None:
        """Build the processors"""

        # Define the data for the java args
        data: dict[str, str] = {
            key: value[self.side] for key, value in self.install_profile.get('data', {}).items()
        } | {
            "INSTALLER": self.installer,
            "MINECRAFT_JAR": self.minecraft_jar,
            "ROOT": self.launcher_dir,
            "SIDE": self.side
        }

        # Execute all processors
        for processor in (bar := loadingbar(
            self.install_profile.get('processors', {}),
            title="Installing Forge:",
            disappear=True
        )):
            # Continue if it isn't the right side
            if self.side not in processor.get('sides', ['server', 'client']):
                continue

            # Copy the libraries file to the temp dir
            copyfile(
                path.join(self.launcher_dir, 'libraries', path.normpath(
                    self.libraries[processor['jar']]['path'])),
                (temp_file := path.join(self.temp_dir, path.basename(
                    self.libraries[processor['jar']]['path'])))
            )

            # Copy all libraries to the destination jar file
            with ZipFile(
                path.join(self.temp_dir, path.basename(
                    self.libraries[processor['jar']]['path'])), 'a'
            ) as dest_archive:
                for classpath in processor['classpath']:
                    with ZipFile(
                        path.join(self.launcher_dir, 'libraries', path.normpath(
                            self.libraries[classpath]['path'])), 'r'
                    ) as src_archive:
                        for item in src_archive.infolist():
                            # If it's not a class file or it's
                            # the module info file, continue
                            if not item.filename.endswith('.class') or item.filename == 'module-info.class':
                                continue

                            # Copy all class files
                            if item.filename not in dest_archive.namelist():
                                dest_archive.writestr(
                                    item.filename, src_archive.read(item.filename))

            # Get all java args
            args: list[str] = [
                self.replace_arg_vars(arg, data) for arg in processor['args']
            ]

            # Execute the command, raises CalledProcessError when there's an error
            check_call(['java', '-jar', temp_file, *args], stdout=DEVNULL)

            # Refresh the loading bar
            bar.refresh()


class fabric:
    def __init__(
        self, mc_version: str,
        fabric_version: str,
        side: Side,
        install_dir: str = MINECRAFT_DIR,
        launcher_dir: str = MINECRAFT_DIR
    ) -> None:
        """
        Installs a specified forge version

        :param mc_version: The minecraft version, for example `'1.20.1'`
        :param forge_version: The forge version, for example `'47.1.0'`
        :param side: The side; `'client'` or `'server'`
        :param install_dir: The directory minecraft forge gets installed
        :param launcher_dir: The launcher dir (ignored if on server side)
        """

        self.mc_version = mc_version

        # Define the class variables
        launcher_dir = install_dir if side == 'server' else launcher_dir

        self.mc_version = mc_version
        self.fabric_version = fabric_version
        self.side: Side = side
        self.install_dir = install_dir
        self.launcher_dir = launcher_dir

        loader = fabric_meta.loader(mc_version, fabric_version)
        self.version_json = loader.profile_json()
        self.libraries = loader.libraries(launcher_dir, side, [{
            'name': f'net.fabricmc:fabric-loader:{self.fabric_version}',
            'url': 'https://maven.fabricmc.net/'
        }])

        # Exit if the launcher hasn't launched once
        if not path.isfile(path.join(launcher_dir, 'launcher_profiles.json')) and side == 'client':
            raise FileNotFoundError(
                "Launch the launcher once before installing fabric.")

        # Download the jar files
        self.download_jar_files()

        # Update version info
        if side == 'client':
            self.update_version_info()

    def generate_server_files(self) -> None:
        ...

    def download_jar_files(self) -> None:
        """Download the jar files"""

        # Download everything
        for library in self.libraries:
            # Make the appropiate directories
            makedirs(path.dirname(library['file']), exist_ok=True)

            # Download the resource
            resp: 'HTTPResponse'
            with (request.urlopen(library['url']) as resp,
                  open(path.join(library['file']), 'wb') as mod_file):
                while True:
                    resp_data = resp.read(1024)
                    if not resp_data:
                        break
                    mod_file.write(resp_data)

    def update_version_info(self) -> None:
        """Update version info and inject launcher profiles"""

        # Create a versions directory
        if not path.isdir(versions := path.join(
                self.launcher_dir, 'versions')):
            mkdir(versions)

        # Add version json and dummy jar
        with open(path.join(versions, self.version_json['id'] + '.json'), 'w') as fp:
            dump(self.version_json, fp)

        with open(path.join(versions, self.version_json['id'] + '.jar'), 'w'):
            pass

        # Inject launcher profiles
        with open(path.join(self.launcher_dir, 'launcher_profiles.json'), 'r') as fp:
            launcher_profiles = load(fp)

        with open(path.join(self.launcher_dir, 'launcher_profiles.json'), 'w') as fp:
            launcher_profiles['profiles'][f'fabric-loader-{self.mc_version}'] = {
                "gameDir": path.abspath(self.install_dir),
                "icon": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAACA"
                        "BAMAAAAxEHz4AAAAGFBMVEUAAAA4NCrb0LTGvKW8spyAem2uppSakn"
                        "5SsnMLAAAAAXRSTlMAQObYZgAAAJ5JREFUaIHt1MENgCAMRmFWYAVX"
                        "cAVXcAVXcH3bhCYNkYjcKO8dSf7v1JASUWdZAlgb0PEmDSMAYYBdGk"
                        "YApgf8ER3SbwRgesAf0BACMD1gB6S9IbkEEBfwY49oNj4lgLhA64C0"
                        "o9R9RABTAvp4SX5kB2TA5y8EEAK4pRrxB9QcA4QBWkj3GCAMUCO/xw"
                        "BhAI/kEsCagCHDY4AwAC3VA6t4zTAMj0OJAAAAAElFTkSuQmCC",
                "lastUsed": "1970-01-02T00:00:00.000Z",
                "lastVersionId": self.version_json['id'],
                "name": f"fabric {self.mc_version}",
                "type": "custom"
            }
            dump(launcher_profiles, fp, indent=2)


def inst_modloader(
    modloader: Modloader,
    modpack_version: str,
    modloader_version: str,
    side: Side,
    install_path: str,
    launcher_path: str
) -> None:
    """
    Installs the modloader. Used internally by media.py

    :param mc_version: The minecraft version
    :param modpack_version: The modpack version
    :param side: The side; `'client'` or `'server'`
    :param install_dir: The directory the modloader gets installed
    :param launcher_dir: The launcher dir (ignored if on server side)
    """

    match modloader:
        case 'forge':
            if side == 'client':
                forge(modpack_version, modloader_version,
                      side, install_path, launcher_path)
            elif side == 'server':
                forge(modpack_version, modloader_version,
                      side, install_path)
        case _:
            print("WARNING: Couldn't install modloader because it isn't supported.")
