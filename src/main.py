from json import load
from os import path, mkdir
from typing import Any, TypeAlias
from install import filesize, media

Media: TypeAlias = dict[str, Any]
MediaList: TypeAlias = list[Media]


def install(manifest_file: str,
            install_path: str = path.join(
                path.dirname(path.realpath(__file__)), '..', 'share', '.minecraft'),
            confirm: bool = True) -> None:
    """
    Install a list of mods, resourcepacks, shaderpacks and config files. Arguments:

    :param manifest_file: This should be a path to a manifest file. The file structure:

    ```json
    {
        "minecraft": {
            "version": "(version)",
            "modloader": "(modloader)-(modloader version)"
        },
        "mods": [
            {
                "type": "(type)",
                "slug": "(slug)",
                "name": "(filename)"
            }
        ],
        "resourcepacks": [
            {
                "type": "(type)",
                "slug": "(slug)",
                "name": "(filename)"
            }
        ],
        "shaderpacks": [
            {
                "type": "(type)",
                "slug": "(slug)",
                "name": "(filename)"
            }
        ]
    }
    ```

    :param install_path: The base path everything should be installed to
    :param confirm: If the user should confirm the download
    """

    # Import the manifest file
    with open(manifest_file) as json_file:
        manifest: Media = load(json_file)

    # Check for validity
    if manifest.get('minecraft', None) is None:
        raise KeyError("The modpack must include a 'minecraft' section.")
    if manifest['minecraft'].get('version', None) is None:
        raise KeyError(
            "The 'minecraft' section must include the minecraft version.")
    if manifest['minecraft'].get('modloader', None) is None or \
            '-' not in manifest['minecraft']['modloader']:
        raise KeyError(
            "The 'minecraft' section must include the modloader " +
            "and version in this format: 'modloader-x.x.x'")

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

    total_size = media.prepare_media(
        0, install_path, mods, resourcepacks, shaderpacks)

    # Give warnings for external sources
    external_media: MediaList = [_media for _media in [mod for mod in mods] +
                                 [resourcepack for resourcepack in resourcepacks] +
                                 [shaderpack for shaderpack in shaderpacks]
                                 if _media['type'] == 'url']
    if len(external_media) != 0:
        print("\nWARNING! Some mods/resourcepacks/shaderpacks are from" +
              " external sources and could harm your system:")
        for _media in external_media:
            print(f"  {_media['slug']} ({_media['name']}): {_media['link']}")

    # Print the mod info
    print(
        f"\n{len(mods)} mods, {len(resourcepacks)} " +
        f"recourcepacks, {len(shaderpacks)} shaderpacks\n" +
        f"Total file size: {filesize.size(total_size, system=filesize.alternative)}")

    # Ask for confirmation if confirm is True and install all modpacks
    if confirm == True:
        if input("Continue? (Y/n) ").lower() not in ['y', '']:
            print("Cancelling...\n")
            exit()
    else:
        print("Continue (Y/n) ")

    # Download all files
    media.download_files(total_size, install_path, mods,
                         resourcepacks, manifest.get('shaderpacks', []))


if __name__ == '__main__':
    current_dir = path.dirname(path.realpath(__file__))

    if (mcm_location := input("Manifest file location (default: example-manifest.json): ")) == '':
        mcm_location = path.join(
            current_dir, '..', 'share', 'modpacks', 'example-manifest.json'
        )

    if (install_location := input("Install location (default: share/.minecraft): ")) == '':
        install_location = path.join(current_dir, '..', 'share', '.minecraft')

        if not path.isdir(install_location):
            mkdir(install_location)

        print('\n', end='')
        install(mcm_location)
    else:
        print('\n', end='')
        install(mcm_location, install_location)
