#!/usr/bin/env python3

import asyncio
import string, argparse, json
import importlib, pkgutil, sys
from dataclasses import dataclass
from typing import List, Dict 
from pathlib import Path

import mudfuzz.mud_fuzzer as MF
import mudfuzz.ui as UI
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand
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


def load_fuzz_commands ( config_cmds ):
    cmd_path = Path ( ".", "mudfuzz", "fuzz_commands" )
    modules = pkgutil.iter_modules ( path=[ cmd_path ] )
    loaded_cmds = dict ()

    for loader, mod_name, ispkg in modules:
        if mod_name in sys.modules:
            continue

        loaded_mod = importlib.import_module (
                f"mudfuzz.fuzz_commands.{mod_name}" )
        class_name = snake_to_camel_case ( mod_name )

        print ( mod_name )
        if mod_name in config_cmds:
            loaded_class = getattr ( loaded_mod, class_name, None )
            instance = loaded_class ()
            probability = config_cmds [ mod_name ]
            loaded_cmds [ instance ] = probability

    return loaded_cmds

def parse_config_file ( f ):
    data = json.load ( f )
    return MudFuzzConfig ( **data )

def load_terms ( terms_path ):
    def r ( x ):
        with open ( x ) as f:
            return [ l.strip() for l in  f.readlines () ]
    return { x.name : r (x) for x in terms_path.iterdir () if x.is_file () }

async def main ( **kwargs ):
    config_data = None

    config_path = Path ( kwargs [ "config_path" ] ).resolve ()

    if not config_path.is_file ():
        print ( f"Unable to open config.json at {config_path}." )
        return

    with ( open (config_path) ) as f:
        config_data = parse_config_file ( f )

    terms = load_terms ( config_path.parent / "terms" )
    fuzz_cmds = load_fuzz_commands ( config_data.fuzz_cmds )
    mudfuzzer = MF.MudFuzzer ( config_data, fuzz_cmds, terms )

    event_cb = print if kwargs [ "no_ui" ] else UI.get_ui_cb ()

    mudfuzzer.start ( event_cb )

    await asyncio.Event().wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser ( description="Mud Fuzz",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter )

    parser.add_argument( "--config", help = "Path to config.json" )

    parser.add_argument( "--no_ui", action="store_true",
            help = "Run without user interface." )

    args = parser.parse_args ()

    try:
        asyncio.run ( main ( config_path=args.config, no_ui=args.no_ui ) )
    except KeyboardInterrupt:
        pass
