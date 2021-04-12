import threading, queue, time
from telnetlib import Telnet

class MudConnection:

    def __init__ ( self, host, port ):
        self.host = host
        self.port = port

        self.send_queue = queue.Queue ()
        self.rcv_queue = queue.Queue ()

        self.telnet_thread = threading.Thread ( target=self._telnet_process,
                                                daemon=True )
        self.telnet_thread.start ()

    def _telnet_process ( self ):
        with Telnet ( self.host, self.port ) as tn:
            while True:
                try:
                    self._read_telnet ( tn )
                except EOFError:
                    break

                try:
                    self._write_telnet ( tn )
                except OSError:
                    break

                time.sleep ( 0.01 )
    
    def _read_telnet ( self, tn ):
        rcv = tn.read_until ( b"\r\n", 0.1 )
        self.rcv_queue.put ( rcv )

    def _write_telnet ( self, tn ):
        try:
            send = self.send_queue.get( block=False )
        except queue.Empty:
            return

        tn.write ( send )


