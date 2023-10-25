from atexit import register
from json import load, loads, dump
from os import path, getenv, mkdir, rename
from shutil import rmtree, copyfile
from subprocess import CalledProcessError, check_call, DEVNULL
from sys import platform
from typing import overload
from urllib import request
from zipfile import ZipFile

from .urls import forge as forge_urls, fabric as fabric_urls
from .loadingbar import loadingbar

from .._types import (
    Client, Server, Side,
    MinecraftJson, VersionJson,
    InstallProfile, Libraries
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
    @overload
    def __init__(self, mc_version: str,
                 forge_version: str,
                 side: Client,
                 install_dir: str = ...,
                 launcher_dir: str = ...) -> None: ...

    @overload
    def __init__(self, mc_version: str,
                 forge_version: str,
                 side: Server,
                 install_dir: str = ...) -> None: ...

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
                "Java was not found in the system's PATH. " +
                "Please make sure you have Java installed and it is properly configured."
            )

        self.minecraft_json: MinecraftJson = loads(request.urlopen(
            [item for item in loads(
                request.urlopen(
                    forge_urls.version_manifest_v2()
                ).read().decode('utf-8')
            )['versions'] if item['id'] == mc_version][0]['url']
        ).read().decode('utf-8'))

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
                self.version_json: VersionJson = load(fp)

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

        # Extract when paths start witn '/'
        if path.normpath(arg).startswith('/') and arg != self.minecraft_jar:
            with ZipFile(self.installer, 'r') as archive:
                archive.extract(arg[1:], self.temp_dir)
            return path.join(self.temp_dir, path.normpath(arg[1:]))

        # Return arg if it isn't "[something]"
        if arg[0] != '[' and arg[-1] != ']':
            return arg

        # Remove the brackets
        arg = arg.replace('[', '').replace(']', '')

        # Split the file extension
        if '@' in arg:
            arg, file_extension = arg.split('@', 1)
        else:
            file_extension = 'jar'

        # Create the file and folder path
        folder = (
            # Until the first colon, replace
            # ':' and '.' with path.sep
            arg[:arg.find(':')]
            .replace(':', '.')
            .replace('.', path.sep) +

            # Then, do the same
            # until the third colon
            (arg[arg.find(':'):]
             if arg.count(':') != 3
             else arg[arg.find(':'):
                      arg.rfind(':')]
             ).replace(':', path.sep)
        )

        file = (
            # Select everything from
            # the first colon and
            # replace ':' with '-'
            arg[arg.find(':')+1:]
            .replace(':', '-') +

            # Add the file extension
            '.' + file_extension)

        # Return the full path
        return path.join(self.launcher_dir, 'libraries', folder, file)

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
            for directory in [path.join(self.launcher_dir, 'versions'),
                              path.join(self.launcher_dir, 'versions', self.mc_version)]:
                if not path.isdir(directory):
                    mkdir(directory)

            # Write the (version).json file
            with open(path.join(self.launcher_dir, 'versions', self.mc_version, f"{self.mc_version}.json"), 'w') as fp:
                dump(self.minecraft_json, fp)

        # Define the download urls
        downloads = {
            self.installer: forge_urls.forge_installer_url(self.mc_version, self.forge_version),
            self.minecraft_jar: self.minecraft_json['downloads'][self.side]['url']
        }

        # Download everything
        for fname, url in downloads.items():
            with request.urlopen(url) as resp:
                with open(path.join(fname), 'wb') as mod_file:
                    while True:
                        resp_data = resp.read(1024)
                        if not resp_data:
                            break
                        mod_file.write(resp_data)

    def install_libraries(self) -> None:
        """Installs all libraries"""

        # Define the java os names
        osdict = {
            "windows": "win32",
            "linux": "linux",
            "osx": "darwin"
        }

        # Define the libaries
        self.libraries: Libraries = {}

        # Add all libraries to the libraries dict
        for library in (self.install_profile.get('libraries', []) +
                        self.version_json.get('libraries', []) +
                        self.minecraft_json.get('libraries', [])):

            # Add the library to libraries
            rules = library.get('rules', [])

            self.libraries[library['name']] = library['downloads']['artifact']
            self.libraries[library['name']].update(rules[-1] if rules else {})

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
            # Don't download if it's not for the current os
            if 'action' in library and library['action'] == 'allow':
                if platform != osdict[library['os']['name']]:
                    bar.update(library['size'])
                    bar.refresh()
                    continue
            if 'action' in library and library['action'] == 'disallow':
                if platform == osdict[library['os']['name']]:
                    bar.update(library['size'])
                    bar.refresh()
                    continue

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
                continue

            # Check if the files don't already exist
            if path.isfile(full_library_path):
                # Just update the bar and continue if they exist
                bar.update(library['size'])
                bar.refresh()
                continue

            # Download the files
            # TODO: Check the sha1
            with request.urlopen(library['url']) as resp:
                with open(full_library_path, 'wb') as mod_file:
                    while True:
                        resp_data = resp.read(1024)
                        if not resp_data:
                            break
                        size = mod_file.write(resp_data)
                        bar.update(size)

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
            with ZipFile(path.join(self.temp_dir, path.basename(self.libraries[processor['jar']]['path'])), 'a') as dest_archive:
                for classpath in processor['classpath']:
                    with ZipFile(path.join(self.launcher_dir, 'libraries', path.normpath(self.libraries[classpath]['path'])), 'r') as src_archive:
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

            # Execute the command
            try:
                check_call(['java', '-jar', temp_file, *args], stdout=DEVNULL)
            except CalledProcessError as e:
                print(e)
                exit(1)

            # Refresh the loading bar
            bar.refresh()


class fabric:
    "I accidentally uploaded this, it's unfinished"

    def __init__(self, mc_version: str,
                 fabric_version: str,
                 side: Side,
                 install_dir: str = MINECRAFT_DIR,
                 launcher_dir: str = MINECRAFT_DIR) -> None:

        self.mc_version = mc_version

        # Define the class variables
        launcher_dir = install_dir if side == 'server' else launcher_dir

        self.mc_version = mc_version
        self.fabric_version = fabric_version
        self.side = side
        self.install_dir = install_dir
        self.launcher_dir = launcher_dir

        self.install_version()

    def install_version(self):
        print(request.urlopen(fabric_urls.api_url(
            'v2', 'versions', 'loader',
            self.mc_version, self.fabric_version,
            'server', 'json'
        )).read().decode('utf-8'))
