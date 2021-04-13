#!/usr/bin/env python3

import time
import re, string, argparse, json
import importlib, pkgutil, sys
from dataclasses import dataclass
from typing import List, Dict, Type
from pathlib import Path

import mudfuzz.ui as UI
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand
from mudfuzz.mud_fuzzer import MudFuzzer
from mudfuzz.util import *

@dataclass
class MudFuzzConfig:
    mud_host: str
    mud_port: str
    user: str
    password: str
    user_prompt: str
    password_prompt: str
    error_pattern: str
    error_pause: bool
    fuzz_cmds: Dict [ str, float ]
    valid_commands: List [ str ]
    valid_words: List [ str ]


def load_fuzz_commands ():
    cmd_path = Path ( ".", "mudfuzz", "fuzz_commands" )
    modules = pkgutil.iter_modules ( path=[ cmd_path ] )
    loaded_cmds = []

    for loader, mod_name, ispkg in modules:
        if mod_name in sys.modules:
            continue

        loaded_mod = importlib.import_module (
                f"mudfuzz.fuzz_commands.{mod_name}" )
        class_name = snake_to_camel_case ( mod_name )
        loaded_class = getattr ( loaded_mod, class_name, None )

        if not loaded_class:
            continue

        instance = loaded_class ()
        loaded_cmds.append ( instance )

    return loaded_cmds

def parse_config_file ( f ):
    data = json.load ( f )
    return MudFuzzConfig ( **data )

def run_no_ui ( config_data, mudfuzz ):
    mudfuzz.start ()

    while True:
        e = mudfuzz.get_fuzz_event ()

        if e is not None:
            print ( e )

def main ( **kwargs ):
    print ( "MUD Fuzz" )

    config_data = None

    with ( open ( kwargs [ "config_path" ] ) ) as f:
        config_data = parse_config_file ( f )

    fuzz_cmds = load_fuzz_commands ()
    mudfuzz = MudFuzzer ( config_data, fuzz_cmds )

    if kwargs [ "no_ui" ]:
        run_no_ui ( config_data, mudfuzz )
    else:
        UI.start_ui ( config_data, mudfuzz )


if __name__ == "__main__":
    parser = argparse.ArgumentParser ( description="Mud Fuzz",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter )

    parser.add_argument( "--config", help = "Path to config.json" )

    parser.add_argument( "--no_ui", action="store_true",
            help = "Run without user interface." )

    args = parser.parse_args ()
    main ( config_path=args.config, no_ui=args.no_ui )
