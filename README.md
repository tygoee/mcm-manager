# Minecraft Modpack Manager

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
      "link": "https://cdn.essential.gg/mods/60ecf53d6b26c76a26d49e5b/649c45fb8b045520b2c1c8b2/Essential-fabric_1-20-1.jar",
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
  ]
}
```

The mod types are `cf`, `mr`, `pm` and `url`

You can get a mod slug &/ id from the mod url:

- https://www.curseforge.com/minecraft/mc-mods/worldedit/download/4586218 -> worldedit, 4586218
- https://modrinth.com/mod/sodium/version/mc1.20.1-0.5.1 -> sodium
- https://www.planetminecraft.com/texture-pack/1-13-1-16-unique-spawn-eggs/ -> 1-13-1-16-unique-spawn-eggs

To get the mod name &/ mod id &/ media type, go to downloads -> the file and copy download link:

- https://mediafilez.forgecdn.net/files/4586/218/worldedit-mod-7.2.15.jar -> worldedit-mod-7.2.15.jar
- https://cdn-raw.modrinth.com/data/AANobbMI/versions/OkwCNtFH/sodium-fabric-mc1.20.1-0.5.1.jar -> AANobbMIOkwCNtFH, sodium-fabric-mc1.20.1-0.5.1.jar
- https://static.planetminecraft.com/files/resource_media/texture/unique-spawn-eggs-v1-5.zip -> texture, unique-spawn-eggs-v1-5.zip

Make sure 'name' is ascii encoded, for example `%20` instead of a space
