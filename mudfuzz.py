#!/usr/bin/env python3

import asyncio
import sys
import argparse
import json
import importlib
import pkgutil
from dataclasses import dataclass
from typing import Dict
from pathlib import Path

import mudfuzz.mud_fuzzer as MF
import mudfuzz.ui as UI
from mudfuzz.util import snake_to_camel_case


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
    fuzz_cmds: Dict[str, float]


def load_fuzz_commands(config_cmds):
    cmd_path = Path(".", "mudfuzz", "fuzz_commands")
    modules = pkgutil.iter_modules(path=[cmd_path])
    loaded_cmds = dict()

    for loader, mod_name, ispkg in modules:
        if mod_name in sys.modules:
            continue

        import_path = f"mudfuzz.fuzz_commands.{mod_name}"
        loaded_mod = importlib.import_module(import_path)
        class_name = snake_to_camel_case(mod_name)

        if mod_name in config_cmds:
            loaded_class = getattr(loaded_mod, class_name, None)
            instance = loaded_class()
            probability = config_cmds[mod_name]
            loaded_cmds[instance] = probability

    return loaded_cmds


def parse_config_dir(d):
    config_path = Path(d).resolve()

    if not config_path.is_dir():
        print(f"Unable to open config dir at {config_path}.")
        sys.exit()
        return

    with open(config_path / "config.json") as f:
        data = json.load(f)
        config_data = MudFuzzConfig(**data)

    fuzz_cmds = load_fuzz_commands(config_data.fuzz_cmds)
    terms = load_terms(config_path / "terms")
    return (config_data, fuzz_cmds, terms)


def load_terms(terms_path):
    def r(path):
        with open(path)as f:
            return[line.strip() for line in f.readlines()]
    return {x.name: r(x) for x in terms_path.iterdir() if x.is_file()}


async def main(**kwargs):
    config_data = parse_config_dir(kwargs["config_path"])
    mudfuzzer = MF.MudFuzzer(*config_data)

    event_cb = print if kwargs["no_ui"]else UI.get_ui_cb()

    mudfuzzer.start(event_cb)

    await asyncio.Event().wait()


if __name__ == "__main__":
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description="Mud Fuzz",
                                     formatter_class=formatter)

    parser.add_argument("config", 
                        help="Path to config directory")

    parser.add_argument("--no_ui",
                        action="store_true",
                        help="Run without user interface.")

    args = parser.parse_args()

    try:
        asyncio.run(main(config_path=args.config, no_ui=args.no_ui))
    except KeyboardInterrupt:
        pass
