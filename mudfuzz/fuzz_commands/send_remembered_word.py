import random
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand

class SendRememberedWord ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        mudfuzz.send_string ( mudfuzz.get_random_remembered_word ())
        mudfuzz.send_string ( random.choice ( [ " ", "\r\n" ] ) )

