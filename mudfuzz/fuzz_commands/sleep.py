import random, time
from fuzz_commands.fuzz_command import FuzzCommand

class Sleep ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        sleeptime = random.random () * 3
        print ( "Sleeping for %f." % sleeptime )
        time.sleep ( sleeptime )

