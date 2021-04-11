import random, string
from fuzz_commands.fuzz_command import FuzzCommand

class SendRandomString ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        r_string = "".join( random.choices(string.printable, 
                            k=random.randint(0,128))) 
        mudfuzz.send_string ( r_string )
