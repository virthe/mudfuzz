import asyncio
import time, threading
import queue
from telnetlib import Telnet


class MudConnection:

    def __init__ ( self, host, port ):
        self.host = host
        self.port = port

        self.input_queue = queue.Queue ()
        self.output_queue = queue.Queue ()

    async def connect ( self ):

        in_thread = threading.Thread ( target = self._read_telnet,
                daemon=True )
        out_thread = threading.Thread ( target = self._write_telnet,
                daemon=True )

        with Telnet ( self.host, self.port ) as tn:

            self.tn = tn
            self.connected = True

            in_thread.start ()
            out_thread.start ()

            while self.connected:
                await asyncio.sleep ( 1 )

    def read ( self ):
        try:
            data = self.output_queue.get ( block=False )
        except queue.Empty:
            return None
        else:
            return data

    def write ( self, data ):
        self.input_queue.put_nowait ( data )

    def _connection_broken ( self ):
        self.connected = False
    
    def _read_telnet ( self ):
        while self.connected:
            try:
                rcv = self.tn.read_until ( b"\r\n", 5 )
            except EOFError:
                self._connection_broken ()
            self.output_queue.put_nowait ( rcv )

    def _write_telnet ( self ):
        while self.connected:
            send = self.input_queue.get ()
            if send is not None:
                try:
                    self.tn.write ( send )
                except OSError:
                    self._connection_broken ()
            time.sleep ( 0.1 )


