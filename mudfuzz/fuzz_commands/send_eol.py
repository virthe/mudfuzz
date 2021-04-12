from fuzz_commands.fuzz_command import FuzzCommand

class SendEol ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        mudfuzz.send_eol ()
