import asyncio 
import random, re
from enum import Flag, auto
from dataclasses import dataclass
from typing import Type
from collections import deque

from mudfuzz.util import *
from mudfuzz.mud_connection import MudConnection

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

    def __init__ ( self, config_data, fuzz_cmds, terms ):
        self.config_data = config_data
        self.connection = None
        self.fuzz_cmds = fuzz_cmds

        self.terms = terms
        self.memory = deque ( [], 300 )
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
            await asyncio.sleep ( 0.5 )

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
            self._do_random_fuzz_cmd ()

    def _do_random_fuzz_cmd ( self ):
        cmds = list ( self.fuzz_cmds.keys () )
        weights = self.fuzz_cmds.values()
        cmd = random.choices ( cmds, weights ) [ 0 ]
        cmd.execute ( self )

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

    def send_term ( self, t=None ):
        k = random.choice (list( self.terms.keys () )) if t is None else t
        v = random.choice ( self.terms [ k ] )
        self.send_string ( v )

    def send_buffer ( self, b ):
        if self.connection is None:
            return

        self.connection.write ( b )
        self._post_fuzz_event ( SentBuffer ( b ) )

    def remember_words ( self, text ):
        text = strip_ansi(text).lower()
        text = re.sub(r'[^a-z0-9 ]', "", text)
        words = [ x for x in text.split(" ") if len(x) > 0 ]
        self.memory.extend ( words )

    def get_random_remembered_word ( self ):
        if len ( self.memory ) < 1:
            return "memory"
        return random.choice ( self.memory ) 

