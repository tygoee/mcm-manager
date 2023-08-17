from os import path, get_terminal_size, mkdir
from tqdm import tqdm
from typing import Any, TypeAlias
from urllib import parse, request, error
from install.headers import headers
from install.url_generator import generate_media_url

Media: TypeAlias = dict[str, Any]
MediaList: TypeAlias = list[Media]


def prepare_media(total_size: int, install_path: str, mods: MediaList,
                  resourcepacks: MediaList, shaderpacks: MediaList) -> int:
    """Get the file size and check media validity while listing all media"""

    def check_media_validity(media_list: MediaList, media_type: str) -> None:
        """Check for the modpack file validity"""
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

    def get_headers(media: Media, total_size: int) -> int:
        """Recieve the content-length headers"""
        try:
            size = int(request.urlopen(
                url).headers.get('content-length', 0))
        except error.HTTPError:
            # When returning an HTTP error, try again
            # while mimicking a common browser user agent
            size = int(request.urlopen(request.Request(
                url, headers=headers)).headers.get('content-length', 0))

        media['_'] += (size,)
        total_size += size

        return total_size

    if len(mods) != 0:
        check_media_validity(mods, 'mod')

        # List the installed mods and prepare the modpack
        print("\nMods:")

        for mod in mods:
            # Add the corresponding url to mod['_']
            url, mod['_'] = generate_media_url(mod, install_path, 'mods')

            # Append the mod size to the total size and save it in mod['_']
            total_size = get_headers(mod, total_size)

            # Print the mod name
            print(f"  {mod['slug']} ({parse.unquote(mod['name'])})")

    if len(resourcepacks) != 0:
        check_media_validity(resourcepacks, 'resourcepack')

        # List the installed resourcepacks and prepare them
        print("\nResourcepacks:")

        for resourcepack in resourcepacks:
            # Add the corresponding url to mod['_']
            url, resourcepack['_'] = generate_media_url(
                resourcepack, install_path, 'resourcepacks')

            # Append the resourcepack size to the total size and save it in mod['_']
            total_size = get_headers(resourcepack, total_size)

            # Print the resourcepack name
            print(
                f"  {resourcepack['slug']} ({parse.unquote(resourcepack['name'])})")

    if len(shaderpacks) != 0:
        check_media_validity(shaderpacks, 'shaderpack')

        # List the installed shaderpacks and prepare them
        print("\nShaderpacks:")

        for shaderpack in shaderpacks:
            # Add the corresponding url to mod['_']
            url, shaderpack['_'] = generate_media_url(
                shaderpack, install_path, 'shaderpacks')

            # Append the shaderpack size to the total size and save it in mod['_']
            total_size = get_headers(shaderpack, total_size)

            # Print the shaderpack name
            print(
                f"  {shaderpack['slug']} ({parse.unquote(shaderpack['name'])})")

    # At the end, return the total mods size
    return total_size


def download_files(total_size: int, install_path: str, mods: MediaList,
                   resourcepacks: MediaList, shaderpacks: MediaList) -> None:
    """Download all files using a tqdm loading bar"""

    for folder, media_list in {
        'mods': mods,
        'resourcepacks': resourcepacks,
        'shaderpacks': shaderpacks
    }.items():
        if len(media_list) != 0 and not path.isdir(path.join(install_path, folder)):
            mkdir(path.join(install_path, folder))

    print('\033[?25l')  # Hide the cursor
    skipped_files = 0

    with tqdm(
        total=total_size,
        position=1,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        bar_format='{desc}'
    ) as outer_bar:
        for url, fname, size in (inner_bar := tqdm(
            [mod['_'] for mod in mods] +
            [resourcepack['_'] for resourcepack in resourcepacks] +
            [shaderpack['_'] for shaderpack in shaderpacks],
            position=0,
            unit='B',
            unit_scale=True,
            total=total_size,
            unit_divisor=1024,
            bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
            leave=False
        )):
            if not path.isfile(fname):
                description = f"Installing {parse.unquote(path.basename(fname))}..."
                if len(description) > get_terminal_size().columns:
                    description = description[:get_terminal_size().columns]

                outer_bar.set_description_str(description)
                try:
                    with request.urlopen(url) as resp:
                        with open(fname, 'wb') as mod_file:
                            while True:
                                data = resp.read(1024)
                                if not data:
                                    break
                                size = mod_file.write(data)
                                inner_bar.update(size)
                                inner_bar.refresh()
                except error.HTTPError:
                    with request.urlopen(request.Request(url, headers=headers)) as resp:
                        with open(fname, 'wb') as mod_file:
                            while True:
                                data = resp.read(1024)
                                if not data:
                                    break
                                size = mod_file.write(data)
                                inner_bar.update(size)
                                inner_bar.refresh()

            else:
                skipped_files += 1

                description = parse.unquote(path.basename(fname)) + \
                    "is already installed, skipping..."
                if len(description) > get_terminal_size().columns:
                    description = description[:get_terminal_size().columns]

                outer_bar.set_description_str(description)

                inner_bar.update(size)
                inner_bar.refresh()

    print('\033[2A\033[?25h')  # Go two lines back and show cursor

    # Make a new bar that directly updates to 100% as
    # the last one will dissapear after the loop is done
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

    print(' ' * (get_terminal_size().columns) + '\r', end='')
    print(
        f"Skipped {skipped_files}/{len(mods) + len(resourcepacks) + len(shaderpacks)} " +
        "files that were already installed" if skipped_files != 0 else ''
    )
