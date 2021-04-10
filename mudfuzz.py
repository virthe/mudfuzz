#!/usr/bin/env python3

import json, threading, queue, time, re, string, random, argparse, os
from telnetlib import Telnet
from enum import Enum, auto
from collections import deque
from dataclasses import dataclass

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

        #SendRandomBytes ( 0.005), 
        self.actions = [ 
                self.FuzzAction ( "abc", 0.05, "sendrandomstring" ), 
                self.FuzzAction ( "abc", 0.25, "sendeol" ), 
                self.FuzzAction ( "abc", 0.1, "sendescape" ), 
                self.FuzzAction ( "abc", 0.2, "sendlook" ), 
                self.FuzzAction ( "abc", 1,  "sendcommand" ),
                self.FuzzAction ( "abc", 0.05,  "sendword"),
                self.FuzzAction ( "abc", 0.1,  "sleep"),
                self.FuzzAction ( "abc", 0.75 ,  "sendrememberedword" )
            ]

        self.memory = deque ( [], 100 )

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

        try:
            text = rcv.decode ( 'utf-8' )
        except:
            print ( "Bad string from MUD" )
            return

        if ( len ( text ) > 0 ):
            print ( text )

        if ( self.state is MudFuzzState.AWAIT_USER ):
           if ( re.search ( self.config_data [ "user_prompt" ], text ) ):
               print ( "User prompt detected." )
               self.send_string ( self.config_data [ "user" ] )
               self.send_eol ()
               self.state = MudFuzzState.AWAIT_PASS
               return

        if ( self.state is MudFuzzState.AWAIT_PASS ):
           if ( re.search ( self.config_data [ "password_prompt" ], text ) ):
               print ( "Password prompt detected." )
               self.send_string ( self.config_data [ "password" ] )
               self.send_eol ()
               self.state = MudFuzzState.FUZZING
               return

        if ( self.state is MudFuzzState.FUZZING ):
            if ( len ( self.actions ) == 0 ):
                return

            self.remember_words ( text )

            weights = [ x.probability for x in self.actions ]
            action = random.choices ( self.actions, weights ) [ 0 ]
            self.execute_action ( action, text )
            return

    def send_string ( self, s ):
        b = s.encode ( "utf-8" )
        self.send_buffer ( b )

    def send_eol ( self ):
        self.send_string ( "\r\n" )

    def send_buffer ( self, b ):
        if ( self.connection is None ):
            return

        try:
            print ( "Sending : %s" % 
                    ( b.decode ( "utf-8" ).encode ( "unicode_escape" ) ) )
        except:
            print ( "Sending garbage." )

        self.connection.send_queue.put_nowait ( b )

    def remember_words ( self, text ):
        try:
            words = strip_ansi(text).strip().split(" ")
        except:
            return

        words = [ x for x in words if len ( x ) > 0 ]

        self.memory.extend ( words )

    def get_random_remembered_word ( self ):
        if ( len ( self.memory ) < 1 ):
            return "memory"
        return random.choice ( self.memory ) 

    @dataclass
    class FuzzAction:
        name: str
        probability: float
        command: str

    def execute_action ( self, action, text ):

        if ( action.command == "sendrandomstring" ):
            r_string = "".join(
            random.choices(string.printable, 
            k=random.randint(0,128))) 
            self.send_string ( r_string )
        if ( action.command == "sendeol" ):
            self.send_eol ()
        if ( action.command == "sendescape" ):
            self.send_eol ()
            self.send_string ( "**" )
            self.send_eol ()
        if ( action.command == "sendlook" ):
            self.send_eol ()
            self.send_string ( "look" )

            if ( random.random () < 0.5 ):
                self.send_string ( " " )
                self.send_string ( self.get_random_remembered_word ())

            self.send_eol ()
        if ( action.command == "sendcommand" ):
            self.send_string ( 
            random.choice ( self.config_data [ "valid_commands" ] ))
            self.send_string ( " " )
        if ( action.command == "sendword" ):
            self.send_string ( 
            random.choice ( self.config_data [ "valid_words" ] ))
            self.send_string ( " " )

        if ( action.command == "sleep" ):
            sleeptime = random.random () * 3
            print ( "Sleeping for %f." % sleeptime )
            time.sleep ( sleeptime )

        if ( action.command == "sendrememberedword" ):
            self.send_string ( self.get_random_remembered_word ())
            self.send_string ( " " )
        if ( action.command == "sendrandombytes" ):
            self.send_buffer ( os.urandom ( random.randint ( 0, 1024 ) ) )

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

def strip_ansi ( text ):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def parse_config_file ( f ):
    data = json.load ( f )
    return data

def main ( **kwargs ):
    print ( "MUD Fuzz" )

    config_data = None

    with ( open ( kwargs [ "config_path" ] ) ) as f:
        config_data = parse_config_file ( f )

    mudfuzz = MudFuzz ( config_data )

    mudfuzz.connect ()

    while True:
        mudfuzz.tick ()
        time.sleep ( 0.1 )

if __name__ == "__main__":
    parser = argparse.ArgumentParser ( description="Mud Fuzz",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser.add_argument( "--config", help = "Path to config.json" )
    args = parser.parse_args ()
    main ( config_path=args.config )
