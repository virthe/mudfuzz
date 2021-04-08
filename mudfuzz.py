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
        tn.read_until ( bytes (  config_data [ "user_prompt" ], "utf-8" ) )
        tn.write ( config_data [ "user" ].encode ('ascii') )
        tn.write ( "\r\n".encode ('ascii') )
        tn.read_until ( bytes (  config_data [ "user_prompt" ], "utf-8" ) )
        tn.write ( config_data [ "password" ].encode ('ascii') )
        tn.write ( "\r\n".encode ('ascii') )
        tn.interact ()

if __name__ == "__main__":
    main ();
