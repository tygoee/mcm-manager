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

from json import load
from os import path, mkdir
from urllib import parse, request, error

from .urls import media_url
from .loadingbar import loadingbar
from .modloaders import inst_modloader, MINECRAFT_DIR
from .filesize import size, alternative

from ..typings import Manifest, URLMedia, Media, MediaList, Side

# The headers to mimic a common browser user agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

class prepare:
    def __init__(self, install_path: str, side: Side, manifest: Manifest) -> None:
        "Get the file size and check media validity while listing all media"

        # Define the class variables
        self.install_path = install_path
        self.side: Side = side

        # Prepare the media
        self.total_size = 0

        for media_type, media_list in {
            'mod': manifest.get('mods', []),
            'resourcepack': manifest.get('resourcepacks', []),
            'shaderpack': manifest.get('shaderpacks', [])
        }.items():
            self._prepare_media(media_type, media_list)

    @classmethod
    def load_manifest(cls, filename: str) -> Manifest:
        "Load a manifest file and validate it's general contents"
        with open(filename) as json_file:
            manifest = load(json_file)

        # Check for validity
        if manifest.get('minecraft') is None:
            raise KeyError("The modpack must include a 'minecraft' section.")
        if manifest['minecraft'].get('version') is None:
            raise KeyError(
                "The 'minecraft' section must include the minecraft version.")
        if manifest['minecraft'].get('modloader') is None or \
                '-' not in manifest['minecraft']['modloader']:
            raise KeyError(
                "The 'minecraft' section must include the modloader " +
                "and version in this format: 'modloader-x.x.x'")

        return manifest

    def _check_media_validity(self, media_list: MediaList, media_type: str) -> None:
        "Check for the modpack file validity"
        for media in media_list:
            for key in ['type', 'slug', 'name']:
                if key not in media:
                    raise KeyError(
                        f"The '{key}' key should be specified " +
                        f"in the following {media_type}: {media}."
                    )
            if media['type'] not in ['cf', 'mr', 'pm', 'url']:
                raise KeyError(
                    f"The type '{media['type']}' does not exist: {media}."
                )

            # Add a media['sides'] to all media, default ['client', 'server']
            sides: list[Side] = ['client', 'server']
            if 'sides' not in media.keys():
                media['sides'] = sides

    def _get_headers(self, media: Media, url: str) -> None:
        "Recieve the content-length headers"
        try:
            size = int(request.urlopen(
                url).headers.get('content-length', 0))
        except error.HTTPError:
            try:
                # When returning an HTTP error, try again
                # while mimicking a common browser user agent
                size = int(request.urlopen(request.Request(
                    url, headers=headers)).headers.get('content-length', 0))
            except error.HTTPError as e:
                print(f"! WARNING: Could not download {media['name']}: \n{e}")

                return
        except error.URLError as e:
            if e.reason.__str__() in ("[Errno -2] Name or service not known", "[Errno 11001] getaddrinfo failed"):
                print(f"! WARNING: The mod {media['name']}" +
                      f"was not found: {e.reason}")
                return
            else:
                raise e

        # Add the size to the tuple and the total size
        if '_dl' in media:
            media['_dl'] = media['_dl'][:-1] + (size,)

        self.total_size += size

    def _prepare_media(self, media_type: str, media_list: MediaList) -> None:
        if len(media_list) == 0:
            return

        self._check_media_validity(media_list, media_type)

        # List the installed media and prepare the modpack
        print(f"\n{media_type.capitalize()}s: ")

        for media in (media for media in media_list if self.side in media['sides']):
            # Add the corresponding download info to media['_dl']
            url = media_url(media)

            dl_path = path.join(
                self.install_path,
                media_type + 's',
                parse.unquote(media['name'])
            )

            media['_dl'] = (url, dl_path, 0)

            # Get the headers for appending the total size
            self._get_headers(media, url)

            # Print the media name
            print(f"  {media['slug']} ({parse.unquote(media['name'])})")


def download_file(url: str, fname: str, bar: loadingbar[int]) -> None:
    try:
        # Download and write the file
        with request.urlopen(url) as resp, open(fname, 'wb') as media_file:
            while True:
                # Read the response data
                data = resp.read(1024)

                # Break if it's complete
                if not data:
                    break

                # Update the bar
                part_size = media_file.write(data)
                bar.update(part_size)

    except error.HTTPError:
        # If the file is denied, it tries again while
        # mimicking a common browser user agent
        try:
            with request.urlopen(
                    request.Request(url, headers=headers)
            ) as resp, open(fname, 'wb') as media_file:
                while True:
                    data = resp.read(1024)
                    if not data:
                        break
                    part_size = media_file.write(data)
                    bar.update(part_size)
        except error.HTTPError:
            pass  # The user has already been warned
    except error.URLError:
        pass  # The user has already been warned


def download_files(total_size: int, install_path: str, side: Side, manifest: Manifest) -> None:
    """
    Download all files with a loading bar

    :param total_size: The total size of all media
    :param install_path: The path it's going to be installed to
    :param side: The side; `'client'` or `'server'`
    :param manifest: The manifest data from `prepare.load_manifest()`
    """

    mods: MediaList = manifest.get('mods', [])
    resourcepacks: MediaList = manifest.get('resourcepacks', [])
    shaderpacks: MediaList = manifest.get('shaderpacks', [])

    for folder, media_list in {
        'mods': mods,
        'resourcepacks': resourcepacks,
        'shaderpacks': shaderpacks
    }.items():
        if len(media_list) != 0 and not path.isdir(path.join(install_path, folder)):
            mkdir(path.join(install_path, folder))

    print('\033[?25l')  # Hide the cursor
    skipped_files = 0

    # Genereate the iterator
    iterator: list[tuple[str, str, int, list[Side]]] = []

    for media in mods + resourcepacks + shaderpacks:
        if "_dl" not in media:
            continue
        item: tuple[str, str, int, list[Side]] = (
            *media['_dl'], media['sides'])
        iterator.append(item)

    # Download everything with a loading bar
    with loadingbar(
        total=total_size,
        unit='B',
        show_desc=True,
        disappear=True
    ) as bar:
        for url, fname, fsize, sides in iterator:
            if side not in sides:
                # As the size isn't calculated, it
                # doesn't have to update the bar
                continue

            if path.isfile(fname):
                skipped_files += 1

                # Inform it's already installed
                bar.update(fsize)
                bar.set_desc(parse.unquote(path.basename(fname)) +
                             " is already installed, skipping...")

                continue

            # Set the description
            file = parse.unquote(path.basename(fname))
            bar.set_desc(f"Downloading {file}...")

            download_file(url, fname, bar)

    print('\033[?25h')  # Show the cursor

    total_files = len([media for media in mods +
                      resourcepacks + shaderpacks if side in media.get('sides', [])])

    print(
        f"Skipped {skipped_files}/{total_files} " +
        "files that were already installed" if skipped_files != 0 else '',
        sep=''
    )


def install(
    manifest_file: str,
    install_path: str = path.join(path.join(path.dirname(
        path.realpath(__file__)), '..'), 'share', '.minecraft'),
    side: Side = 'client',
    install_modloader: bool = True,
    launcher_path: str = MINECRAFT_DIR,
    confirm: bool = True
) -> None:
    """
    Install a list of mods, resourcepacks, shaderpacks and config files. Arguments:

    :param manifest_file: This should be a path to a manifest file. \
                          For the file structure, look at the README
    :param install_path: The base path everything should be installed to
    :param side: `'client'` or `'server'`: The side to be installed
    :param inst_modloader: If you want to install the modloader
    :param launcher_path: The path of your launcher directory
    :param confirm: If the user should confirm the download
    """

    # Import the manifest file
    manifest = prepare.load_manifest(manifest_file)

    # List the modpack info
    modpack_version: str = manifest['minecraft']['version']
    modloader: str = manifest['minecraft']['modloader'].split(
        '-', maxsplit=1)[0]
    modloader_version: str = manifest['minecraft']['modloader'].split(
        '-', maxsplit=1)[1]

    print(f"Modpack version: {modpack_version}\n" +
          f"Mod loader: {modloader}\n"
          f"Mod loader version: {modloader_version}")

    mods: MediaList = manifest.get('mods', [])
    resourcepacks: MediaList = manifest.get('resourcepacks', [])
    shaderpacks: MediaList = manifest.get('shaderpacks', [])

    total_size = prepare(install_path, side, manifest).total_size

    # Give warnings for external sources
    external_media: list[URLMedia] = [_media for _media in [mod for mod in mods] +
                                      [resourcepack for resourcepack in resourcepacks] +
                                      [shaderpack for shaderpack in shaderpacks]
                                      if _media['type'] == 'url']
    if len(external_media) != 0:
        print("\nWARNING! Some mods/resourcepacks/shaderpacks are from"
              " external sources and could harm your system:")
        for _media in external_media:
            print(f"  {_media['slug']} ({_media['name']}): {_media['url']}")

    # Print the mod info
    print(
        f"\n{len(mods)} mods, {len(resourcepacks)} "
        f"recourcepacks, {len(shaderpacks)} shaderpacks\n"
        f"Total file size: {size(total_size, system=alternative)}"
    )

    # Ask for confirmation if confirm is True and install all modpacks
    if confirm:
        try:
            if input("Continue? (Y/n) ").lower() not in ['y', '']:
                print("Cancelling...\n")
                exit()
        except KeyboardInterrupt:
            print(end='\n')
            exit(130)

    # Download and install the modloader
    if install_modloader:
        inst_modloader(modloader, modpack_version, modloader_version,
                       side, install_path, launcher_path)

    # Download all files
    download_files(total_size, install_path, side, manifest)
