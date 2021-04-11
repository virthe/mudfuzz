class SendLook ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        mudfuzz.send_eol ()
        mudfuzz.send_string ( "look" )

        if ( random.random () < 0.5 ):
            mudfuzz.send_string ( " " )
            mudfuzz.send_string ( mudfuzz.get_random_remembered_word ())

        mudfuzz.send_eol ()

