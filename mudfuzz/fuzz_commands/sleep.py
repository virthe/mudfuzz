import random, time
from mudfuzz.fuzz_commands.fuzz_command import FuzzCommand

class Sleep ( FuzzCommand ):
    def execute ( self, mudfuzz ):
        sleeptime = random.random () * 3
        time.sleep ( sleeptime )

