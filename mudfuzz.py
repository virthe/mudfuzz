#!/usr/bin/env python3

import json, threading, queue, time, re
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

        try:
            rcv = self.connection.rcv_queue.get ( block=False )
        except queue.Empty:
            pass
        else:
            self._process_incoming_data ( rcv )

    def _process_incoming_data ( self, rcv ):

        text = rcv.decode ( 'utf-8' )

        if ( len ( text ) > 0 ):
            print ( text )

        if ( self.state is MudFuzzState.AWAIT_USER ):
           if ( re.search ( self.config_data [ "user_prompt" ], text ) ):
               print ( "User prompt detected." )
               self._send_string ( self.config_data [ "user" ] )
               self.state = MudFuzzState.AWAIT_PASS

        if ( self.state is MudFuzzState.AWAIT_PASS ):
           if ( re.search ( self.config_data [ "password_prompt" ], text ) ):
               print ( "Password prompt detected." )
               self._send_string ( self.config_data [ "password" ] )
               self.state = MudFuzzState.AWAIT_PASS

    def _send_string ( self, s ):

        s += "\r\n"

        if ( self.connection is None ):
            return
        b = s.encode ( 'utf-8' )
        self.connection.send_queue.put_nowait ( b )

class MudConnection:

    def __init__ ( self, host, port ):
        self.host = host
        self.port = port

        self.send_queue = queue.Queue ()
        self.rcv_queue = queue.Queue ()

        self.telnet_thread = threading.Thread ( target=self._telnet_process,
                                                daemon=True )
        self.telnet_thread.start ()

    def _telnet_process ( self ):
        with Telnet ( self.host, self.port ) as tn:
            while True:
                try:
                    rcv = tn.read_until ( b"\r\n", 0.1 )
                    self.rcv_queue.put ( rcv )
                except EOFError:
                    break

                try:
                    send = self.send_queue.get( block=False )
                except queue.Empty:
                    pass
                else:
                    try:
                        tn.write ( send )
                    except OSError:
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

if __name__ == "__main__":
    main ();
