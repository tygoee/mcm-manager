from json import load
from os import path, get_terminal_size, mkdir
from tqdm import tqdm
from urllib import parse, request, error

from install.headers import headers
from install.urls import media_url

from _types import Media, Manifest, MediaList, Side


class prepare:
    def __new__(cls, install_path: str, side: Side, mods: MediaList,
                resourcepacks: MediaList, shaderpacks: MediaList) -> int:
        "Get the file size and check media validity while listing all media"

        # Define the class variables
        cls.install_path = install_path
        cls.side: Side = side

        # Prepare the media
        total_size = 0

        for media_type, media_list in {
            'mod': mods,
            'resourcepack': resourcepacks,
            'shaderpack': shaderpacks
        }.items():
            total_size += cls.prepare_media(media_type, media_list, total_size)

        # At the end, return the total mods size
        return total_size

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

    @classmethod
    def check_media_validity(cls, media_list: MediaList, media_type: str) -> None:
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

    @classmethod
    def get_headers(cls, media: Media, url: str, total_size: int) -> int:
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

                return total_size
        except error.URLError as e:
            if e.reason.__str__() in ("[Errno -2] Name or service not known", "[Errno 11001] getaddrinfo failed"):
                print(f"! WARNING: The mod {media['name']} was not found: {e.reason}")  # noqa
                return total_size
            else:
                raise e

        # Add the size to the tuple
        media['_dl'] = media['_dl'][:-1] + (size,)
        total_size += size

        return total_size

    @classmethod
    def prepare_media(cls, media_type: str, media_list: MediaList, total_size: int) -> int:
        if len(media_list) == 0:
            return total_size

        cls.check_media_validity(media_list, media_type)

        # List the installed media and prepare the modpack
        print(f"\n{media_type.capitalize()}s: ")

        for media in (media for media in media_list if cls.side in media['sides']):
            # Add the corresponding url to media['_dl']
            url, media['_dl'] = media_url(
                media, cls.install_path, media_type + 's')

            # Append the media size to the total size and save it in media['_dl']
            total_size = cls.get_headers(media, url, total_size)

            # Print the media name
            print(f"  {media['slug']} ({parse.unquote(media['name'])})")

        # At the end, return the total media size
        return total_size


def download_files(total_size: int, install_path: str, side: Side, mods: MediaList,
                   resourcepacks: MediaList, shaderpacks: MediaList) -> None:
    "Download all files using a tqdm loading bar"

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
        item: tuple[str, str, int, list[Side]
                    ] = (*media['_dl'], media['sides'])
        iterator.append(item)

    # Download everything with a loading bar
    with tqdm(
        total=total_size,
        position=1,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        bar_format='{desc}'
    ) as outer_bar:
        for url, fname, size, sides in (inner_bar := tqdm(
            iterator,
            position=0,
            unit='B',
            unit_scale=True,
            total=total_size,
            unit_divisor=1024,
            bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
            leave=False
        )):
            if side not in sides:
                # As the size isn't calculated, it
                # doesn't have to update the bar
                continue

            if path.isfile(fname):
                skipped_files += 1

                # Prepare the description
                description = parse.unquote(path.basename(fname)) + \
                    "is already installed, skipping..."

                # Cut off the description if it's longer than terminal width
                if len(description) > get_terminal_size().columns:
                    description = description[:get_terminal_size().columns]

                # Inform it's already installed
                outer_bar.set_description_str(description)

                # Upadate and refresh the bar
                inner_bar.update(size)
                inner_bar.refresh()

                continue

            # Prepare the description
            description = f"Downloading {
                parse.unquote(path.basename(fname))}..."

            # Cut off the description if it's longer than terminal width
            if len(description) > get_terminal_size().columns:
                description = description[:get_terminal_size().columns]

            # Set the description string
            outer_bar.set_description_str(description)

            try:
                # Download the file
                with request.urlopen(url) as resp:
                    # Write the file
                    with open(fname, 'wb') as media_file:
                        while True:
                            # Read the response data
                            data = resp.read(1024)

                            # Break if it's complete
                            if not data:
                                break

                            # Update the bar
                            size = media_file.write(data)
                            inner_bar.update(size)
                            inner_bar.refresh()
            except error.HTTPError:
                # If the file is denied, it tries again while
                # mimicking a common browser user agent
                try:
                    with request.urlopen(request.Request(url, headers=headers)) as resp:
                        with open(fname, 'wb') as media_file:
                            while True:
                                data = resp.read(1024)
                                if not data:
                                    break
                                size = media_file.write(data)
                                inner_bar.update(size)
                                inner_bar.refresh()
                except error.HTTPError:
                    description = "WARNING: Could not download " + \
                        parse.unquote(path.basename(fname))

                    if len(description) > get_terminal_size().columns:
                        description = description[:get_terminal_size().columns]

                    outer_bar.set_description_str(description)
            except error.URLError:
                description = "WARNING: The mod " + \
                    parse.unquote(path.basename(fname)) + \
                    "was not found"

                if len(description) > get_terminal_size().columns:
                    description = description[:get_terminal_size().columns]

                outer_bar.set_description_str(description)

    print('\033[2A\033[?25h')  # Go two lines back and show cursor

    # Make a new bar that directly updates to 100% as
    # the last one will dissapear after the loop is done
    # (Dissapears automatically if also installing mods)
    if total_size != 0:
        with tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}'
        ) as bar:
            bar.update(total_size)
    else:
        with tqdm(
            total=1,
            unit='it',
            bar_format='{percentage:3.0f}%|{bar}| 0.00/0.00'
        ) as bar:
            bar.update(1)

    total_files = len([media for media in mods +
                      resourcepacks + shaderpacks if side in media['sides']])

    print(' ' * get_terminal_size().columns + '\r',
          f"Skipped {skipped_files}/{total_files} " +
          "files that were already installed" if skipped_files != 0 else '',
          sep=''
          )
