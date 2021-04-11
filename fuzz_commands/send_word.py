class SendWord ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        mudfuzz.send_string ( 
        random.choice ( mudfuzz.config_data.valid_words ))
        mudfuzz.send_string ( " " )

