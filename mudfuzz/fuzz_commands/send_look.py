import random
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand

class SendLook ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        mudfuzz.send_eol ()
        mudfuzz.send_string ( "look" )

        if ( random.random () < 0.5 ):
            mudfuzz.send_string ( " " )
            mudfuzz.send_string ( mudfuzz.get_random_remembered_word ())

        mudfuzz.send_eol ()

