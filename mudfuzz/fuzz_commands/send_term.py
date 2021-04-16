import random
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand

class SendTerm ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        mudfuzz.send_term ()
        mudfuzz.send_string ( random.choice ( [ " ", "\r\n" ] ) )

