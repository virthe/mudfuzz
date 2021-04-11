import random, string

class SendRandomString ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        r_string = "".join( random.choices(string.printable, 
                            k=random.randint(0,128))) 
        mudfuzz.send_string ( r_string )
