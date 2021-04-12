import random
from fuzz_commands.fuzz_command import FuzzCommand

class SendWord ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        mudfuzz.send_string ( 
        random.choice ( mudfuzz.config_data.valid_words ))
        mudfuzz.send_string ( " " )

