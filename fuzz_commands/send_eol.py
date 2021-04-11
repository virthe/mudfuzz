class SendEOL ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        mudfuzz.send_eol ()
