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

from argparse import ArgumentParser
from dataclasses import dataclass, fields
from os import path, makedirs
from typing import Any, Literal, Optional, TypedDict, TypeVar

from .install.media import install
from .install.modloaders import MINECRAFT_DIR
from .typings import Side


class Options(TypedDict):
    manifest_file: str
    install_path: str
    side: Side
    install_modloader: bool
    launcher_path: str
    confirm: bool


@dataclass(init=False)
class _Args:
    # Positional arguments
    pos: Literal[False] | str

    # Options
    y: bool            # confirm installation
    o: bool            # skip modloader install
    m: Optional[str]   # manifest
    i: Optional[str]   # install path
    s: Optional[Side]  # side
    l: Optional[str]   # launcher path

    def __init__(self, **kwargs: Any) -> None:
        """Ignore non-existent names"""
        names = set(f.name for f in fields(self))
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


class parse:
    current_dir = path.dirname(path.realpath(__file__))
    app_root = path.join(path.dirname(path.realpath(__file__)), '..')

    def __new__(cls) -> _Args:
        # Make a parser
        cls.parser = ArgumentParser(
            prog="mcm-manager",
            description="Minecraft Modpack Manager"
        )

        # Add positional arguments
        cls.parser.add_argument(
            'pos', nargs='?', default=False, metavar='cli',
            help='use a cli interface to install a modloader'
        )

        cls.parser.add_argument(
            'install', nargs='?', default=False,
            help='install a package directly'
        )

        # Define optional arguments
        optional_args: list[tuple[tuple[str, ...], str, str] | tuple[tuple[str, ...], str]] = [
            (('-y', '--yes'), "continue installation without confirmation"),
            (('-m',), 'MANIFEST', "specify the manifest file to load"),
            (('-i',), 'INSTPATH', "specify the path where it will be installed"),
            (('-s',), 'SIDE', "specify the side to be installed (client or server)"),
            (('-l',), 'LAUNCHERPATH', "specify the path of the launcher"),
            (('-o',), "skip the installation of the modloader"),
        ]

        # Add optional arguments
        for arg in optional_args:
            if len(arg) == 3:
                cls.parser.add_argument(
                    *arg[0], metavar=arg[1],
                    help=arg[2]
                )
            else:
                cls.parser.add_argument(
                    *arg[0], action='store_true',
                    dest=arg[0][0][1], help=arg[1]
                )

        # Get the args and execute the right function
        return _Args(**vars(cls.parser.parse_args()))

    @classmethod
    def _cli(cls, args: _Args):
        """Ask questions and execute `install()` with the answers"""

        _T = TypeVar("_T")

        def ask(arg: _T | None, question: _T) -> _T | str:
            return input(question) if arg is None else arg

        def ask_yes(arg: _T, question: _T) -> bool:
            return input(question).lower() == 'y' if arg else arg

        # Define all questions
        questions = [
            "Manifest file location (default: example-manifest.json): ",
            "Install location (default: share/gamedir): ",
            "Install side (client/server, default: client): ",
            "Do you want to install the modloader? (y/N, default: n): ",
            f"Launcher location (default: {MINECRAFT_DIR}): "
        ]

        # Ask all questions
        try:
            answers: Options = {
                "manifest_file": ask(args.m, questions[0]),
                "install_path": ask(args.i, questions[1]),
                "side": 'server' if ask(args.s, questions[2]) == 'server' else 'client',
                "install_modloader": (inst_modl := ask_yes(not args.o, questions[3])),
                "launcher_path": ask(args.l, questions[4]) if inst_modl else '',
                "confirm": not args.y
            }
        except KeyboardInterrupt:
            print(end='\n')
            exit(130)

        # Set the defaults
        defaults = {
            "manifest_file": path.join(cls.current_dir, '..', 'share', 'modpacks', 'example-manifest.json'),
            "install_path": path.join(cls.current_dir, '..', 'share', 'gamedir'),
            "launcher_path": MINECRAFT_DIR
        }

        # Cycle through them and apply
        for default in defaults:
            if answers[default] == '':
                answers[default] = defaults[default]

        # Make the install directory if it's nonexistent
        if not path.isdir(answers["install_path"]):
            makedirs(answers["install_path"])

        print('\n', end='')

        # Install
        install(**answers)

    @classmethod
    def execute(cls, args: _Args):
        if args.s not in ('client', 'server') and args.s is not None:
            raise TypeError(
                "side has to be either 'client', 'server' or None.")

        match args.pos:
            case 'cli':
                cls._cli(args)
            case 'install':
                # Set the defaults
                options: Options = {
                    "manifest_file": args.m or path.join(cls.current_dir, '..', 'share',
                                                         'modpacks', 'example-manifest.json'),
                    "install_path": args.i or path.join(cls.current_dir, '..', 'share', 'gamedir'),
                    "side": 'server' if args.s == 'server' else 'client',
                    "install_modloader": (inst_modl := not args.o),
                    "launcher_path": args.l if args.l is not None and inst_modl else MINECRAFT_DIR,
                    "confirm": not args.y
                }

                install(**options)

            case _:
                # TODO else, execute the gui (not finished)
                raise NotImplementedError(
                    "Calling without any (or invalid) positional arguments will open a gui, "
                    "but this is not implemented yet.\n" + cls.parser.format_usage()
                )


def main():
    # Get the command-line arguments
    args = parse()

    # Execute the right function
    parse.execute(args)
