import time, queue
from telnetlib import Telnet

from mudfuzz.io_thread import IOThread

class MudConnection:

    def __init__ ( self, host, port ):
        self.host = host
        self.port = port

        self.tn_thread = IOThread ( self._telnet_process )

    def read ( self ):
        try:
            data = self.tn_thread.output_queue.get ( block=False )
        except queue.Empty:
            return None
        else:
            return data

    def write ( self, data ):
        self.tn_thread.input_queue.put_nowait ( data )

    def _telnet_process ( self, input_queue, output_queue ):
        with Telnet ( self.host, self.port ) as tn:
            while True:
                try:
                    self._read_telnet ( tn, output_queue )
                except EOFError:
                    break

                try:
                    self._write_telnet ( tn, input_queue )
                except OSError:
                    break

                time.sleep ( 0.01 )
    
    def _read_telnet ( self, tn, output_queue ):
        rcv = tn.read_until ( b"\r\n", 0.1 )
        output_queue.put ( rcv )

    def _write_telnet ( self, tn, input_queue ):
        try:
            send = input_queue.get( block=False )
        except queue.Empty:
            return

        tn.write ( send )


