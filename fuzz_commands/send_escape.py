from fuzz_commands.fuzz_command import FuzzCommand

class SendEscape ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        mudfuzz.send_eol ()
        mudfuzz.send_string ( "**" )
        mudfuzz.send_eol ()
