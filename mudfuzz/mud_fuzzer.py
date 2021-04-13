import time, threading
import random, re
from enum import Flag, auto
from dataclasses import dataclass
from typing import Type
from collections import deque

from mudfuzz.util import *
from mudfuzz.mud_connection import MudConnection
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand

@dataclass
class MudFuzzEvent:
    pass

@dataclass
class ReceivedText:
    text: str

@dataclass
class ReceivedGarbled:
    size: int

class FuzzerState(Flag):
    START = auto()
    CONNECTING = auto()
    AWAIT_USER = auto()
    AWAIT_PASS = auto()
    FUZZING = auto ()
    USER_PAUSE = auto ()
    ERROR_PAUSE = auto ()
    PAUSE = USER_PAUSE | ERROR_PAUSE

class MudFuzzer:

    def __init__ ( self, config_data, fuzz_cmd_instances ):
        self.config_data = config_data
        self.state = FuzzerState.START
        self.connection = None
        self.fuzz_cmd_instances = fuzz_cmd_instances

        #Create FuzzAction list from fuzz_cmds in config
        cmd_inst = lambda x : self.get_cmd_instance ( x [ 0 ] )
        self.actions = [ self.FuzzAction ( *x, cmd_inst( x ) ) for x in \
                config_data.fuzz_cmds.items() ]

        self.memory = deque ( [], 100 )
        self.max_reads = 100

    def start ( self ):
        if self.state is not FuzzerState.START:
            return

        self._connect ()
        
        self.thread = threading.Thread ( target=self._run, 
                daemon=True )
        self.thread.start ()

    def _run ( self ):
        while True:
            self._tick ()
            time.sleep ( 0.1 )


    def _connect ( self ):
        if self.state is not FuzzerState.START:
            return
        self.state = FuzzerState.CONNECTING

        self.connection = MudConnection ( self.config_data.mud_host,
                                          self.config_data.mud_port )
        self.state = FuzzerState.AWAIT_USER

    def _tick ( self ):
        if self.connection is None:
            return

        print ( self.state )

        if self.is_paused ():
            print("Paused")
            return

        for _ in range ( self.max_reads ):
            rcv = self.connection.read ()

            if rcv is not None:
                self._process_incoming_data ( rcv )
            else:
                break

        if self.state is FuzzerState.FUZZING:
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
            print ( text, end="" )

        if re.search ( self.config_data.error_pattern, text ):
            self.error_detected ()
            if self.config_data.error_pause:
                self.pause ( FuzzerState.ERROR_PAUSE, self.state )
                return

        if self.state is FuzzerState.AWAIT_USER:
           if re.search ( self.config_data.user_prompt, text ):
               print ( "User prompt detected." )
               self.send_string ( self.config_data.user )
               self.send_eol ()
               self.state = FuzzerState.AWAIT_PASS
               return

        if self.state is FuzzerState.AWAIT_PASS:
           if re.search ( self.config_data.password_prompt, text ):
               print ( "Password prompt detected." )
               self.send_string ( self.config_data.password )
               self.send_eol ()
               self.state = FuzzerState.FUZZING
               return

        if self.state is FuzzerState.FUZZING:
            self.remember_words ( text )

    def error_detected ( self ):
        print ( "Error detected!" )

    def pause ( self, pause_state, unpause_state ):
        if not pause_state & FuzzerState.PAUSE:
            raise Exception ( "Bad pause state." )
        if unpause_state & FuzzerState.PAUSE:
            raise Exception ( "Bad unpause state." )
        self.state = pause_state
        self.unpause_state = unpause_state

    def is_paused ( self ):
        return self.state & FuzzerState.PAUSE

    def unpause ( self ):
        if not self.is_paused ():
            raise Exception ( "Called unpause when not paused." )
        self.state = self.unpause_state
        delattr ( self, "unpause_state" )

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

        self.connection.write ( b )

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

