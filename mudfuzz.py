#!/usr/bin/env python3

import threading, queue, time
import random
import re, string, argparse, json
import importlib, os, pkgutil, sys
from telnetlib import Telnet
from enum import Enum, auto
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Type
from fuzz_commands.fuzz_command import FuzzCommand

@dataclass
class MudFuzzConfig:
    mud_host: str
    mud_port: str
    user: str
    password: str
    user_prompt: str
    password_prompt: str
    fuzz_cmds: Dict [ str, float ]
    valid_commands: List [ str ]
    valid_words: List [ str ]

class MudFuzzState(Enum):
    START = auto()
    CONNECTING = auto()
    AWAIT_USER = auto()
    AWAIT_PASS = auto()
    FUZZING = auto ()

class MudFuzz:

    def __init__ ( self, config_data, fuzz_cmd_instances ):
        self.config_data = config_data
        self.state = MudFuzzState.START
        self.connection = None
        self.fuzz_cmd_instances = fuzz_cmd_instances

        #Create FuzzAction list from fuzz_cmds in config
        cmd_inst = lambda x : self.get_cmd_instance ( x [ 0 ] )
        self.actions = [ self.FuzzAction ( *x, cmd_inst( x ) ) for x in \
                config_data.fuzz_cmds.items() ]

        self.memory = deque ( [], 100 )
        self.max_reads = 100

    def connect ( self ):
        if self.state is not MudFuzzState.START:
            return
        self.state = MudFuzzState.CONNECTING

        self.connection = MudConnection ( self.config_data.mud_host,
                                          self.config_data.mud_port )
        self.state = MudFuzzState.AWAIT_USER

    def tick ( self ):
        if self.connection is None:
            return

        for _ in range ( self.max_reads ):
            try:
                rcv = self.connection.rcv_queue.get ( block=False )
                self._process_incoming_data ( rcv )
            except queue.Empty:
                break

        if self.state is MudFuzzState.FUZZING:
            if len ( self.actions ) > 0:
                weights = [ x.probability for x in self.actions ]
                action = random.choices ( self.actions, weights ) [ 0 ]
                self.execute_action ( action )
                return

    def _process_incoming_data ( self, rcv ):
        try:
            text = rcv.decode ( 'utf-8' )
        except:
            print ( "Bad string from MUD" )
            return

        if len ( text ) > 0:
            print ( text )

        if self.state is MudFuzzState.AWAIT_USER:
           if re.search ( self.config_data.user_prompt, text ):
               print ( "User prompt detected." )
               self.send_string ( self.config_data.user )
               self.send_eol ()
               self.state = MudFuzzState.AWAIT_PASS
               return

        if self.state is MudFuzzState.AWAIT_PASS:
           if re.search ( self.config_data.password_prompt, text ):
               print ( "Password prompt detected." )
               self.send_string ( self.config_data.password )
               self.send_eol ()
               self.state = MudFuzzState.FUZZING
               return

        if self.state is MudFuzzState.FUZZING:
            self.remember_words ( text )

    def send_string ( self, s ):
        b = s.encode ( "utf-8" )
        self.send_buffer ( b )

    def send_eol ( self ):
        self.send_string ( "\r\n" )

    def send_buffer ( self, b ):
        if self.connection is None:
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
        if len ( self.memory ) < 1:
            return "memory"
        return random.choice ( self.memory ) 

    @dataclass
    class FuzzAction:
        cmd_str: str
        probability: float
        cmd_instance: Type[FuzzCommand]

    def get_cmd_instance ( self, cmd_str ):
        cmd_classname = snake_to_camel_case ( cmd_str )

        match = lambda x : x.__class__.__name__ == cmd_classname
        matching_cmds = [ x for x in self.fuzz_cmd_instances if match ( x ) ]

        if len ( matching_cmds ) < 1:
            raise Exception ( f"Unknown command: {cmd_str}" )

        return matching_cmds [ 0 ]

    def execute_action ( self, action ):
        action.cmd_instance.execute ( self )


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
                    self._read_telnet ( tn )
                except EOFError:
                    break

                try:
                    self._write_telnet ( tn )
                except OSError:
                    break

                time.sleep ( 0.01 )
    
    def _read_telnet ( self, tn ):
        rcv = tn.read_until ( b"\r\n", 0.1 )
        self.rcv_queue.put ( rcv )

    def _write_telnet ( self, tn ):
        try:
            send = self.send_queue.get( block=False )
        except queue.Empty:
            return

        tn.write ( send )

def strip_ansi ( text ):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def snake_to_camel_case ( text ):
    return "".join([x.title() for x in text.split("_")])

def load_fuzz_commands ():
    cmd_path = os.path.join ( os.path.dirname ( __file__ ), 
                              "fuzz_commands" )
    modules = pkgutil.iter_modules ( path=[ cmd_path ] )

    loaded_cmds = []

    for loader, mod_name, ispkg in modules:
        if mod_name in sys.modules:
            continue

        loaded_mod = importlib.import_module (f"fuzz_commands.{mod_name}" )

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

def main ( **kwargs ):
    print ( "MUD Fuzz" )

    config_data = None

    with ( open ( kwargs [ "config_path" ] ) ) as f:
        config_data = parse_config_file ( f )

    fuzz_cmds = load_fuzz_commands ()

    mudfuzz = MudFuzz ( config_data, fuzz_cmds )

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
