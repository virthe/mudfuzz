class SendRandomBytes ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        mudfuzz.send_buffer ( os.urandom ( random.randint ( 0, 1024 ) ) )

