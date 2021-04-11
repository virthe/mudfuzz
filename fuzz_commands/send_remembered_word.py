class SendRememberedWord ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        mudfuzz.send_string ( mudfuzz.get_random_remembered_word ())
        mudfuzz.send_string ( " " )

