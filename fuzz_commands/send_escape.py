class SendEscape ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        mudfuzz.send_eol ()
        mudfuzz.send_string ( "**" )
        mudfuzz.send_eol ()
