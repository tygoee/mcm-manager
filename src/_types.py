from typing import TypedDict, Literal


# --- main.py --- #
class Answers(TypedDict):
    manifest_file: str
    install_path: str
    side: Literal['client', 'server']
    install_modloader: bool
    launcher_path: str
