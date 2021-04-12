import random
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand

class SendCommand ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        mudfuzz.send_string ( 
        random.choice ( mudfuzz.config_data.valid_commands ))
        mudfuzz.send_string ( " " )

