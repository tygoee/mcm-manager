# Minecraft Modpack Manager

[![Version](https://img.shields.io/github/v/release/tygoee/mcm-manager?display_name=tag)](https://github.com/tygoee/mcm-manager/releases/latest)
[![License](https://img.shields.io/github/license/tygoee/mcm-manager)](https://www.gnu.org/licenses/gpl-3.0.en.html)
![Repo size](https://img.shields.io/github/repo-size/tygoee/mcm-manager?logo=github)

Minecraft modpack manager - This solves the problem of having to install mods manually. Currently, you need to edit the file manually, as this is still in it's alpha phase. You can currently download mods from curseforge, modrinth and planet minecraft and custom urls. You can also install forge automatically. Currently, mods, resourcepacks and shaderpacks are supported.

## "Building" to a `.pyz` file

How to make a `.pyz` file:

1. Clone the git repository (don't cd into it)

```shell
git clone https://github.com/tygoee/mcm_manager.git
```

2. Using python `zipapp`, make a pyz file

```shell
python3 -m zipapp mcm_manager/ -m src.runner:main
```

To run it

```shell
python3 mcm-manager.pyz
```

To make it an app always accessible from the command line in Unix/Linux, add the [shebang](<https://en.wikipedia.org/wiki/Shebang_(Unix)>) `#!/usr/bin/python3` at the start of the `.pyz` file and copy it to `~/.local/bin/`.

## Creating a mcm file

The mod types are `cf`, `mr`, `pm` and `url`

You can get a mod slug/id from the download page url (which you copy from the url bar or by going to downloads → the file → right click → Go to download page):

- https://www.curseforge.com/minecraft/mc-mods/worldedit/download/4586218  
  ├ `slug` = worldedit  
  └ `id` = 4586218

- https://modrinth.com/mod/sodium/version/mc1.20.1-0.5.1  
  └ `slug` = sodium
- https://www.planetminecraft.com/texture-pack/1-13-1-16-unique-spawn-eggs/  
  └ `slug` = 1-13-1-16-unique-spawn-eggs

To get the rest of the information, go to downloads → the file → right click → the download url:

- https://mediafilez.forgecdn.net/files/4586/218/worldedit-mod-7.2.15.jar  
  └ `name` = worldedit-mod-7.2.15.jar
- https://cdn-raw.modrinth.com/data/AANobbMI/versions/OkwCNtFH/sodium-fabric-mc1.20.1-0.5.1.jar  
  ├ `id` = AANobbMIOkwCNtFH,  
  └ `name` = sodium-fabric-mc1.20.1-0.5.1.jar

- https://static.planetminecraft.com/files/resource_media/texture/unique-spawn-eggs-v1-5.zip  
  ├ `media` texture  
  └ `name` unique-spawn-eggs-v1-5.zip

Make sure 'name' is url encoded, for example `%20` instead of a space

## File structure

Currently you unfortunately need to make the file manually, but for that reason I'll probably make a GUI in the future.

This is what the file structure of an .mcm file should be:

```jsonc
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

An example file:

```jsonc
{
  "minecraft": {
    "version": "1.20.1",
    "modloader": "fabric-0.14.22"
  },
  "mods": [
    {
      "type": "cf", // curseforge
      "slug": "worldedit",
      "name": "worldedit-mod-7.2.15.jar",
      "id": 4586218
    },
    {
      "type": "mr", // modrinth
      "slug": "sodium",
      "name": "sodium-fabric-mc1.20.1-0.5.1.jar",
      "id": "AANobbMIOkwCNtFH"
    },
    {
      "type": "url", // custom url
      "slug": "essential", // doesn't matter
      "name": "Essential-fabric_1-20-1.jar",
      "url": "https://cdn.essential.gg/mods/60ecf53d6b26c76a26d49e5b/649c45fb8b045520b2c1c8b2/Essential-fabric_1-20-1.jar",
      "info": {
        "title": "Essential",
        "icon": "https://static.essential.gg/icon/256x256.png",
        "description": "Essential is a quality of life mod that boosts Minecraft Java to the next level."
      } // info isn't yet implemented
    }
  ],
  "resourcepacks": [
    {
      "type": "pm", // planet minecraft
      "slug": "1-13-1-16-unique-spawn-eggs",
      "name": "unique-spawn-eggs-v1-5.zip",
      "media": "texture"
    }
  ],
  "shaderpacks": [
    {
      "type": "cf",
      "slug": "complementary-shaders",
      "name": "ComplementaryShaders_v4.7.2.zip",
      "id": 4570482
    }
  ]
}
```
