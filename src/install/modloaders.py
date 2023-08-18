from atexit import register
from json import load, loads, dump
from os import path, getenv, mkdir, rename
from shutil import rmtree, copyfile
from subprocess import CalledProcessError, check_call, DEVNULL
from sys import platform
from time import sleep
from tqdm import tqdm
from typing import Any, TypeAlias, Literal, overload
from urllib import request
from zipfile import ZipFile

# Define the minecraft directory
if platform == "win32":
    minecraft_dir = path.join(getenv('APPDATA', ''), ".minecraft")
elif platform == "linux":
    minecraft_dir = path.join(path.expanduser("~"), ".minecraft")
elif platform == "darwin":
    minecraft_dir = path.join(path.expanduser("~"),
                              "Library", "Application Support", "minecraft")
else:
    raise OSError("This OS isn't supported for installing the modloader")


def delete_temp_dir(self: 'forge') -> None:
    if path.isdir(self.temp_dir):
        rmtree(self.temp_dir)  # type: ignore


class forge:
    Libraries: TypeAlias = dict[str, dict[str, Any]]

    @overload
    def __init__(self, mc_version: str,
                 forge_version: str,
                 side: Literal['server'],
                 install_dir: str = ...) -> None: ...

    @overload
    def __init__(self, mc_version: str,
                 forge_version: str,
                 side: Literal['client'],
                 install_dir: str = ...,
                 launcher_dir: str = ...) -> None: ...

    def __init__(self, mc_version: str,
                 forge_version: str,
                 side: Literal['client', 'server'] = 'client',
                 install_dir: str = minecraft_dir,
                 launcher_dir: str = minecraft_dir,) -> None:
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
        self.side = side
        self.install_dir = install_dir
        self.launcher_dir = launcher_dir

        self.temp_dir = path.join(launcher_dir, 'temp')
        self.installer = path.join(
            self.temp_dir, f'forge-{mc_version}-{forge_version}-installer.jar')

        if side == 'client':
            self.minecraft_jar = path.join(launcher_dir, 'versions',
                                           mc_version, f"{mc_version}.jar")
        else:
            self.minecraft_jar = path.join(self.temp_dir, f"{mc_version}.jar")

        self.minecraft_json: dict[str, Any] = loads(request.urlopen(
            [item for item in loads(
                request.urlopen(
                    "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json").read().decode('utf-8')
            )['versions'] if item['id'] == mc_version][0]['url']
        ).read().decode('utf-8'))

        if not path.isfile(path.join(launcher_dir, 'launcher_profiles.json')) and side == 'client':
            raise FileNotFoundError(
                "Launch the launcher once before installing forge.")

        # Download the jar files
        self.download_jar_files()

        # Load all the json data
        with ZipFile(self.installer, 'r') as archive:
            with archive.open('install_profile.json') as fp:
                self.install_profile: dict[str, Any] = load(fp)
            with archive.open('version.json') as fp:
                self.version_json: dict[str, Any] = load(fp)

            forge_dir = path.join(
                launcher_dir, 'versions', f"{mc_version}-forge-{forge_version}")

            if not path.isfile(path.join(forge_dir, f"{mc_version}-forge-{forge_version}.json")) and side == 'client':
                if not path.isdir(forge_dir):
                    mkdir(forge_dir)

                archive.extract('version.json', forge_dir)
                rename(path.join(forge_dir, 'version.json'),
                       path.join(forge_dir, f"{mc_version}-forge-{forge_version}.json"))

        # Inject launcher profiles
        if side == 'client':
            with open(path.join(launcher_dir, 'launcher_profiles.json'), 'r+') as fp:
                launcher_profiles = load(fp)
                launcher_profiles['profiles']['forge'] = {
                    "gameDir": install_dir,
                    "icon": self.install_profile['icon'],
                    "lastUsed": "1970-01-02T00:00:00.000Z",
                    "lastVersionId": self.version_json['id'],
                    "name": "forge",
                    "type": "custom"
                }
                fp.seek(0)  # Move cursor to start of file
                dump(launcher_profiles, fp, indent=2)

        # Install all libraries
        self.install_libraries()

        # Build the processors
        self.build_processors()

    def replace_arg_vars(self, arg: str, data: dict[str, str]) -> str:
        arg = arg.format(**data)

        if path.normpath(arg).startswith(path.sep):
            with ZipFile(self.installer, 'r') as archive:
                archive.extract(arg[1:], self.temp_dir)
            return path.join(self.temp_dir, path.normpath(arg[1:]))

        if not arg.startswith('[') and not arg.endswith(']'):
            return arg

        arg = arg.replace('[', '').replace(']', '')

        if '@' in arg:
            arg, file_extension = arg.split('@', 1)
        else:
            file_extension = 'jar'

        folder = arg[:arg.find(':')].replace(':', '.').replace('.', path.sep) + (arg[arg.find(
            ':'):] if arg.count(':') != 3 else arg[arg.find(':'):arg.rfind(':')]).replace(':', path.sep)

        file = arg[arg.find(':')+1:].replace(':', '-') + '.' + file_extension

        return path.join(self.launcher_dir, 'libraries', folder, file)

    def download_jar_files(self) -> None:
        """Download the jar files"""
        if not path.isdir(self.temp_dir):
            mkdir(self.temp_dir)
        else:
            rmtree(self.temp_dir)
            mkdir(self.temp_dir)

        register(delete_temp_dir, self)  # Delete the temp dir on exit

        if self.side == 'client':
            for directory in [path.join(self.launcher_dir, 'versions'),
                              path.join(self.launcher_dir, 'versions', self.mc_version)]:
                if not path.isdir(directory):
                    mkdir(directory)

            with open(path.join(self.launcher_dir, 'versions', self.mc_version, f"{self.mc_version}.json"), 'w') as fp:
                dump(self.minecraft_json, fp)

        installer_url = "https://maven.minecraftforge.net/net/minecraftforge/forge/" + \
            f"{self.mc_version}-{self.forge_version}/forge-{self.mc_version}-{self.forge_version}-installer.jar"

        downloads = {self.installer: installer_url,
                     self.minecraft_jar: self.minecraft_json['downloads'][self.side]['url']}

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

        self.libraries: forge.Libraries = {
            library['name']: library['downloads']['artifact'] |
            library.get('rules', [{}])[0]
            for library in self.install_profile.get('libraries', []) +
            self.version_json.get('libraries', []) +
            self.minecraft_json.get('libraries', [])
        }

        osdict = {
            "windows": "win32",
            "linux": "linux",
            "osx": "darwin"
        }

        total_size = sum([library['size']
                         for library in self.libraries.values()])

        for library in (bar := tqdm(
            self.libraries.values(),
            unit='B',
            unit_scale=True,
            total=total_size,
            unit_divisor=1024,
            bar_format='Downloading Forge: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
            leave=False
        )):
            # Don't download if it's not for the current os
            if library.get('action', '') == 'allow':
                if platform != osdict[library['os']['name']]:
                    bar.update(library['size'])
                    bar.refresh()
                    continue

            library_path: str = path.normpath(library['path'])

            # Make the directories to place the files in
            for index, directory in enumerate(
                splitted_path := ['libraries', *library_path.split(path.sep)[:-1]]
            ):
                if not path.isdir(joined_path := path.join(self.launcher_dir, *splitted_path[:index], directory)):
                    mkdir(joined_path)

            # Download the files if they don't already exist
            # TODO: Check the sha1
            if path.isfile(path.join(self.launcher_dir, 'libraries', library_path)):
                # Just update the bar and continue if they exist
                bar.update(library['size'])
                bar.refresh()
                continue

            with request.urlopen(library['url']) as resp:
                with open(path.join(self.launcher_dir, 'libraries', library_path), 'wb') as mod_file:
                    while True:
                        resp_data = resp.read(1024)
                        if not resp_data:
                            break
                        size = mod_file.write(resp_data)
                        bar.update(size)

        # # Make a new bar that directly updates to 100% as
        # # the last one will dissapear after the loop is done
        # if total_size != 0:
        #     with tqdm(
        #         total=total_size,
        #         unit='B',
        #         unit_scale=True,
        #         unit_divisor=1024,
        #         bar_format='Downloading Forge: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}'
        #     ) as bar:
        #         bar.update(total_size)
        # else:
        #     with tqdm(
        #         total=1,
        #         unit='it',
        #         bar_format='Downloading Forge: {percentage:3.0f}%|{bar}| 0.00/0.00'
        #     ) as bar:
        #         bar.update(1)

    def build_processors(self) -> None:
        """Build the processors"""

        data: dict[str, str] = {key: value[self.side] for key, value in self.install_profile.get('data', {}).items()} | {
            "INSTALLER": self.installer, "MINECRAFT_JAR": self.minecraft_jar,
            "ROOT": self.launcher_dir, "SIDE": self.side}

        for processor in (bar := tqdm(
            self.install_profile.get('processors', {Any: Any}),
            # total=total_size,
            bar_format=' Installing Forge: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
            leave=False
        )):
            processor: dict[str, Any]

            if self.side not in processor.get('sides', ['server', 'client']):
                continue

            copyfile(
                path.join(
                    self.launcher_dir, 'libraries', path.normpath(self.libraries[processor['jar']]['path'])),
                (temp_file := path.join(
                    self.temp_dir, path.basename(self.libraries[processor['jar']]['path'])))
            )

            with ZipFile(path.join(self.temp_dir, path.basename(self.libraries[processor['jar']]['path'])), 'a') as dest_archive:
                for classpath in processor['classpath']:
                    with ZipFile(path.join(self.launcher_dir, 'libraries', path.normpath(self.libraries[classpath]['path'])), 'r') as src_archive:
                        for item in src_archive.infolist():
                            if not item.filename.endswith('.class') or item.filename == 'module-info.class':
                                continue

                            # Copy all class files
                            if item.filename not in dest_archive.namelist():
                                dest_archive.writestr(
                                    item.filename, src_archive.read(item.filename))

            args: list[str] = [
                self.replace_arg_vars(arg, data) for arg in processor['args']
            ]

            try:
                check_call(['java', '-jar', temp_file, *args],
                           stdout=DEVNULL)
            except CalledProcessError as e:
                print(e)
                exit()

            bar.refresh()
            sleep(1)  # Avoid read/write conflicts


if __name__ == '__main__':
    install_dir = path.realpath(path.join(path.dirname(
        path.realpath(__file__)), '..', '..', 'share', '.minecraft'))

    forge('1.20.1', '47.1.0', 'client', install_dir)
