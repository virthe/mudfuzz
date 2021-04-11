from fuzz_commands.fuzz_command import FuzzCommand

class SendCommand ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        mudfuzz.send_string ( 
        random.choice ( mudfuzz.config_data.valid_commands ))
        mudfuzz.send_string ( " " )

