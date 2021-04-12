import random, os
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand

class SendRandomBytes ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        mudfuzz.send_buffer ( os.urandom ( random.randint ( 0, 1024 ) ) )

