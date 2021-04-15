import time, threading
import queue
from telnetlib import Telnet


class MudConnection:

    def __init__ ( self, host, port ):
        self.host = host
        self.port = port

        self.input_queue = queue.Queue ()
        self.output_queue = queue.Queue ()

        self.thread = threading.Thread ( target=self._telnet_process, 
                daemon=True )
        self.thread.start ()


    def read ( self ):
        try:
            data = self.output_queue.get ( block=False )
        except queue.Empty:
            return None
        else:
            return data

    def write ( self, data ):
        self.input_queue.put_nowait ( data )

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

                time.sleep ( 0.1 )
    
    def _read_telnet ( self, tn ):
        rcv = tn.read_until ( b"\r\n", 0.1 )
        self.output_queue.put_nowait ( rcv )

    def _write_telnet ( self, tn ):
        while not self.input_queue.empty ():
            send = self.input_queue.get (block=False)
            if send is not None:
                tn.write ( send )


