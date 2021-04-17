import asyncio
import time
import threading
import queue
from telnetlib import Telnet


class MudConnection:

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()

        self.connected = False

    def connect(self):
        asyncio.create_task(self._monitor_connection())

    def read(self):
        try:
            data = self.output_queue.get(block=False)
        except queue.Empty:
            return None
        else:
            return data

    def write(self, data):
        self.input_queue.put_nowait(data)

    async def _monitor_connection(self):

        in_thread = threading.Thread(target=self._read_telnet,
                                     daemon=True)
        out_thread = threading.Thread(target=self._write_telnet,
                                      daemon=True)

        with Telnet(self.host, self.port)as tn:

            self.tn = tn
            self.connected = True

            in_thread.start()
            out_thread.start()

            while self.connected:
                await asyncio.sleep(1)

    def _connection_broken(self):
        self.connected = False

    def _read_telnet(self):
        while self.connected:
            try:
                rcv = self.tn.read_until(b"\r\n", 0.5)
            except EOFError:
                self._connection_broken()
                return
            self.output_queue.put_nowait(rcv)

    def _write_telnet(self):
        while self.connected:
            while not self.input_queue.empty():
                send = self.input_queue.get()
                try:
                    self.tn.write(send)
                except OSError:
                    self._connection_broken()
                    return
            time.sleep(0.5)
