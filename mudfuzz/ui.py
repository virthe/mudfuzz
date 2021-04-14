import threading, time

from prompt_toolkit import Application
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.filters import Always
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

import mudfuzz.mud_fuzzer as MF
from mudfuzz.util import *

def start_ui ( config_data, mudfuzzer ):
    rcv_text = Buffer()
    sent_text = Buffer()

    root_container = VSplit([
        Window(content=BufferControl(rcv_text)),
        Window(width=1, char='|'),
        Window(content=BufferControl(sent_text))
    ])

    layout = Layout ( root_container )

    kb = KeyBindings ()

    @kb.add('c-c')
    def _(event):
        event.app.exit ()

    app = Application ( full_screen=True, layout=layout, key_bindings=kb )
    app.rcv_text = rcv_text
    app.sent_text = sent_text
    mf_monitor = MudfuzzMonitor ( app, mudfuzzer )
    app.run ()

class MudfuzzMonitor:
    def __init__ ( self, app, mudfuzzer ):
        self.app = app
        self.mudfuzzer = mudfuzzer
        thread = threading.Thread ( target=self.mudfuzz_thread, daemon=True )
        thread.start ()

    def mudfuzz_thread ( self ):
        self.mudfuzzer.start ()
        while True:
            while not self.mudfuzzer.fuzz_event_queue.empty ():
                handle_mudfuzzer_event ( self.app, 
                                         self.mudfuzzer.get_fuzz_event () )
            time.sleep ( 0.1 )

def handle_mudfuzzer_event ( app, mudfuzzer_event ):

    if ( type(mudfuzzer_event) is MF.ReceivedText ):
        control = app.rcv_text
        display_text ( app, control, f"{mudfuzzer_event.text}" )

    if ( type(mudfuzzer_event) is MF.SentText ):
        control = app.sent_text
        display_text (  app, control, f"{mudfuzzer_event.text}" + "\n" )

def display_text ( app, control, text ):
    control.insert_text ( strip_ansi ( text ) )
    app.invalidate ()
