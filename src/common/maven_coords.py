from os import path


def maven_parse(arg: str) -> tuple[str, str]:
    """
    Parse java maven coords to a folder and a file.

    Example:
    ```txt
    de.oceanlabs.mcp:mcp_config:1.20.1-20230612.114412@zip
    - folder: de/oceanlabs/mcp/mcp_config/1.20.1-20230612.114412/
    - file: mcp_config-1.20.1-20230612.114412.zip
    ```
    maven_"""

    # Split the file extension
    if '@' in arg:
        arg, ext = arg.split('@', 1)
    else:
        ext = 'jar'

    # Until the third colon, replace
    # ':' with path.sep. Until the
    # first, also replace '.' with it
    colons = 0
    folder = ''
    for char in arg:
        if colons == 3:
            folder += path.sep
            break
        if char == ':':
            colons += 1
            char = path.sep
        elif char == '.' and colons == 0:
            char = path.sep
        folder += char

    # Select everything from the first
    # colon and replace ':' with '-'
    file = ''
    for char in arg[arg.find(':')+1:]:
        if char == ':':
            char = '-'
        file += char

    # Add the file extension
    file += '.' + ext

    return folder, file


def maven_to_file(*paths: str) -> str:
    """
    Create a file path from a maven coord.
    The last argument should be `arg`
    """
    return path.join(*paths[:-1], *maven_parse(paths[-1]))


def maven_to_url(base: str, arg: str) -> str:
    """Create a url from a maven coord"""
    if not base[-1] == '/':
        base += '/'

    return ''.join((base, *maven_parse(arg)))
