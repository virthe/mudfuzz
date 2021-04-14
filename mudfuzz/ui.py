import threading, time

from prompt_toolkit import Application
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.filters import Always
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

import mudfuzz.mud_fuzzer as MF
from mudfuzz.util import *

def start_ui ( config_data, mudfuzzer ):

    title_str = "░█▄▒▄█░█▒█░█▀▄▒█▀░█▒█░▀█▀░▀█▀\n"+ \
                "░█▒▀▒█░▀▄█▒█▄▀░█▀░▀▄█░█▄▄░█▄▄"

    rcv_text = Buffer()
    sent_text = Buffer()

    buffer_container = VSplit([
        Window(content=BufferControl(rcv_text)),
        Window(width=1, char='|'),
        Window(content=BufferControl(sent_text))
    ])

    root_container = HSplit([
        Window(height=2, content=FormattedTextControl(text=title_str)),
        Window(height=1, char='-'),
        buffer_container
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
        display_text ( app, control, mudfuzzer_event.text )

    if ( type(mudfuzzer_event) is MF.SentBuffer ):
        control = app.sent_text
        text = mudfuzzer_event.b.decode ( encoding="utf-8", errors="replace" )
        display_text (  app, control, text )

def display_text ( app, control, text ):
    text = strip_ansi ( text )
    text = text.replace ( "\r", "" )
    control.insert_text ( text )
    app.invalidate ()
