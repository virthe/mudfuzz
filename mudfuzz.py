#!/usr/bin/env python3

import json
from telnetlib import Telnet

def parse_config_file ( f ):
    data = json.load ( f )
    return data

def main ():
    print ( "MUD Fuzz" )

    config_data = None

    with ( open ( 'config.json' ) ) as f:
        config_data = parse_config_file ( f )

    with Telnet ( config_data["mud_host"], config_data["mud_port"] ) as tn:
        tn.interact ()

if __name__ == "__main__":
    main ();
