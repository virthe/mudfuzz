import asyncio 
import random, re
from enum import Flag, auto
from dataclasses import dataclass
from typing import Type
from collections import deque

from mudfuzz.util import *
from mudfuzz.mud_connection import MudConnection
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand

class MudFuzzerState(Flag):
    START = auto()
    CONNECTING = auto()
    AWAIT_USER = auto()
    AWAIT_PASS = auto()
    FUZZING = auto ()
    USER_PAUSE = auto ()
    ERROR_PAUSE = auto ()
    PAUSE = USER_PAUSE | ERROR_PAUSE

@dataclass
class MudFuzzerEvent:
    pass

@dataclass
class ReceivedText ( MudFuzzerEvent ):
    text: str

@dataclass
class ReceivedGarbled ( MudFuzzerEvent ):
    size: int

@dataclass
class SentBuffer ( MudFuzzerEvent ):
    b: bytes

@dataclass
class ErrorDetected ( MudFuzzerEvent ):
    pass

@dataclass
class FuzzerStateChanged ( MudFuzzerEvent ):
    state: Type [ MudFuzzerState ]

class MudFuzzer:

    def __init__ ( self, config_data, fuzz_cmd_instances ):
        self.config_data = config_data
        self.connection = None
        self.fuzz_cmd_instances = fuzz_cmd_instances

        #Create FuzzAction list from fuzz_cmds in config
        cmd_inst = lambda x : self.get_cmd_instance ( x [ 0 ] )
        self.actions = [ self.FuzzAction ( *x, cmd_inst( x ) ) for x in \
                config_data.fuzz_cmds.items() ]

        self.memory = deque ( [], 100 )
        self.max_reads = 100

        self.event_cb = None
        self._change_state ( MudFuzzerState.START )

    def start ( self, event_cb ):
        if self.state is not MudFuzzerState.START:
            return

        self.event_cb = event_cb
        self._connect ()

        asyncio.create_task ( self._run () )

    async def _run ( self ):
        while True:
            self._tick ()
            await asyncio.sleep ( 0.1 )

    def _post_fuzz_event ( self, e ):
        if self.event_cb is not None:
            self.event_cb ( e )

    def _connect ( self ):
        if self.state is not MudFuzzerState.START:
            return
        self._change_state ( MudFuzzerState.CONNECTING )

        self.connection = MudConnection ( self.config_data.mud_host,
                                          self.config_data.mud_port )
        self.connection.connect ()
        self._change_state ( MudFuzzerState.AWAIT_USER )

    def _tick ( self ):
        if self.connection is None:
            return

        if self.is_paused ():
            return

        for _ in range ( self.max_reads ):
            rcv = self.connection.read ()

            if rcv is not None:
                self._process_incoming_data ( rcv )
            else:
                break

        if self.state is MudFuzzerState.FUZZING:
            if len ( self.actions ) > 0:
                weights = [ x.probability for x in self.actions ]
                action = random.choices ( self.actions, weights ) [ 0 ]
                self.execute_action ( action )
                return

    def _change_state ( self, s ):
        self.state = s
        self._post_fuzz_event ( FuzzerStateChanged ( s ) )

    def _process_incoming_data ( self, rcv ):
        try:
            text = rcv.decode ( 'utf-8' )
        except:
            self._post_fuzz_event ( ReceivedGarbled ( len ( rcv ) ) )
            return

        if len ( text ) > 0:
            self._post_fuzz_event ( ReceivedText ( text ) )

        if re.search ( self.config_data.error_pattern, text ):
            self.error_detected ()
            if self.config_data.error_pause:
                self.pause ( MudFuzzerState.ERROR_PAUSE, self.state )
                return

        if self.state is MudFuzzerState.AWAIT_USER:
           if re.search ( self.config_data.user_prompt, text ):
               self.send_string ( self.config_data.user )
               self.send_eol ()
               self._change_state ( MudFuzzerState.AWAIT_PASS )
               return

        if self.state is MudFuzzerState.AWAIT_PASS:
           if re.search ( self.config_data.password_prompt, text ):
               self.send_string ( self.config_data.password )
               self.send_eol ()
               self._change_state ( MudFuzzerState.FUZZING )
               return

        if self.state is MudFuzzerState.FUZZING:
            self.remember_words ( text )

    def error_detected ( self ):
        self._post_fuzz_event ( ErrorDetected () )

    def pause ( self, pause_state, unpause_state ):
        if not pause_state & MudFuzzerState.PAUSE:
            raise Exception ( "Bad pause state." )
        if unpause_state & MudFuzzerState.PAUSE:
            raise Exception ( "Bad unpause state." )
        self._change_state ( pause_state )
        self.unpause_state = unpause_state

    def is_paused ( self ):
        return self.state & MudFuzzerState.PAUSE

    def unpause ( self ):
        if not self.is_paused ():
            raise Exception ( "Called unpause when not paused." )
        self._change_state ( self.unpause_state )
        delattr ( self, "unpause_state" )

    def send_string ( self, s ):
        b = s.encode ( "utf-8" )
        self.send_buffer ( b )

    def send_eol ( self ):
        self.send_string ( "\r\n" )

    def send_buffer ( self, b ):
        if self.connection is None:
            return

        self.connection.write ( b )
        self._post_fuzz_event ( SentBuffer ( b ) )

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

