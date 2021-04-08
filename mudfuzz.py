#!/usr/bin/env python3

import json, threading, queue, time
from telnetlib import Telnet
from enum import Enum, auto

class MudFuzzState(Enum):
    START = auto()
    CONNECTING = auto()
    AWAIT_USER = auto()
    AWAIT_PASS = auto()
    FUZZING = auto ()

class MudFuzz:

    def __init__ ( self, config_data ):
        self.config_data = config_data
        self.state = MudFuzzState.START
        self.connection = None

    def connect ( self ):
        if ( self.state is not MudFuzzState.START ):
            return
        self.state = MudFuzzState.CONNECTING

        self.connection = MudConnection ( self.config_data [ "mud_host" ],
                                          self.config_data [ "mud_port" ] )
        self.state = MudFuzzState.AWAIT_USER

    def tick ( self ):
        if ( self.connection is None ):
            return

        rcv = self.connection.rcv_queue.get ()

        if ( len ( rcv ) > 0 ):
            print ( rcv )

class MudConnection:

    def __init__ ( self, host, port ):
        self.host = host
        self.port = port

        self.send_queue = queue.Queue ()
        self.rcv_queue = queue.Queue ()

        self.rcv_thread = threading.Thread ( target=self._telnet_rcv,
                                             daemon=True )
        self.rcv_thread.start ()

    def _telnet_rcv ( self ):
        with Telnet ( self.host, self.port ) as tn:
            while True:
                try:
                    rcv = tn.read_until ( b"\r\n", 0.1 )
                    self.rcv_queue.put ( rcv )
                except EOFError:
                    break
            time.sleep ( 0.1 )


def parse_config_file ( f ):
    data = json.load ( f )
    return data

def main ():
    print ( "MUD Fuzz" )

    config_data = None

    with ( open ( 'config.json' ) ) as f:
        config_data = parse_config_file ( f )

    mudfuzz = MudFuzz ( config_data )

    mudfuzz.connect ()

    while True:
        mudfuzz.tick ()
        time.sleep ( 0.1 )

        #tn.read_until ( bytes (  config_data [ "user_prompt" ], "utf-8" ) )
        #print ( "User prompt")
        #tn.write ( config_data [ "user" ].encode ('utf-8') )
        #tn.write ( "\r\n".encode ('utf-8') )
        #tn.read_until ( bytes (  config_data [ "user_prompt" ], "utf-8" ) )
        #tn.write ( config_data [ "password" ].encode ('utf-8') )
        #tn.write ( "\r\n".encode ('utf-8') )
        #tn.interact ()

if __name__ == "__main__":
    main ();
