import threading, queue

class IOThread:
    """
    A thread with associated input/ouput queues for communication.
    """

    def __init__ ( self, run_cb ):
        self.run_cb = run_cb

        self.input_queue = queue.Queue ()
        self.output_queue = queue.Queue ()

        self.thread = threading.Thread ( target=self.run, daemon=True )

        self.thread.start ()

    def run ( self ):
        self.run_cb ( self.input_queue, self.output_queue )
