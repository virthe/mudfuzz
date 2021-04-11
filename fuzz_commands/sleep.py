import random, time

class Sleep ( FuzzCommand ):
    def execute ( self, mudfuzz, text ):
        sleeptime = random.random () * 3
        print ( "Sleeping for %f." % sleeptime )
        time.sleep ( sleeptime )

