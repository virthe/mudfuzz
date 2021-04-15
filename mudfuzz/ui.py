from dataclasses import dataclass

from prompt_toolkit import Application
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.filters import Always
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

import mudfuzz.mud_fuzzer as MF
from mudfuzz.util import *

def start_ui ( config_data, mudfuzzer ):

    title_str = "░█▄▒▄█░█▒█░█▀▄▒█▀░█▒█░▀█▀░▀█▀\n"+ \
                "░█▒▀▒█░▀▄█▒█▄▀░█▀░▀▄█░█▄▄░█▄▄"

    title=FormattedText([("#ffff00",title_str)])

    rcv_text = ScrollingTextDisplay()
    sent_text = ScrollingTextDisplay()

    sent_rcv_container = VSplit([
        Window(content=rcv_text.content ),
        Window(width=1, char='|'),
        Window(content=sent_text.content)
    ])

    status_display = StatusDisplay ()

    root_container = HSplit([
        Window(height=2, content=FormattedTextControl(text=title)),
        Window(height=1, char='-'),
        sent_rcv_container,
        Window(height=1, char='-'),
        status_display.window
    ])

    layout = Layout ( root_container )

    kb = KeyBindings ()

    @kb.add('c-c')
    def _(event):
        event.app.exit ()

    style = Style([
        ("status_name", "#aa8800"),
        ("status_value", "#00cc00")
    ])
    app = Application ( full_screen=True, layout=layout, key_bindings=kb,
            style=style )
    app.rcv_text = rcv_text
    app.sent_text = sent_text
    app.status_display = status_display

    cb = lambda e : handle_mudfuzzer_event ( app, e )
    mf_monitor = MF.MudfuzzMonitor ( mudfuzzer, cb )
    app.run ()

class ScrollingTextDisplay:
    def __init__ ( self ):
        self.buffer =  Buffer () 
        self.content = BufferControl ( self.buffer )

    def display_text ( self, text ):
        buff=self.buffer
        text = strip_ansi ( text )
        text = text.replace ( "\r", "" )
        buff.insert_text ( text )

        if buff.document.line_count > 200:
            buff.cursor_position = 0
            buff.cursor_down ( 100 )
            buff.delete_before_cursor ( buff.cursor_position )
            buff.cursor_position = len ( buff.document.text )

@dataclass
class Status:
    fuzzer_state:str="INIT"
    error_count:int=0

class StatusDisplay:
    def __init__ ( self ):
        self.content=FormattedTextControl()
        self.window = Window(height=1, content=self.content )
        self.status=Status()

    def update_display ( self ):
        self.content.text= FormattedText ([
            ( "class:status_name", "State: " ),
            ( "class:status_value", f"{self.status.fuzzer_state}" ),
            ("", " "),
            ( "class:status_name", "Errors: " ),
            ( "class:status_value", f"{self.status.error_count}" )
        ])

def handle_mudfuzzer_event ( app, mudfuzzer_event ):

    if ( type(mudfuzzer_event) is MF.FuzzerStateChanged ):
        s = mudfuzzer_event.state
        app.status_display.status.fuzzer_state = s.name
        app.status_display.update_display ()
        app.invalidate ()

    if ( type(mudfuzzer_event) is MF.ErrorDetected ):
        app.status_display.status.error_count += 1
        app.status_display.update_display ()
        app.invalidate ()

    if ( type(mudfuzzer_event) is MF.ReceivedText ):
        control = app.rcv_text
        app.rcv_text.display_text ( mudfuzzer_event.text )
        app.invalidate ()

    if ( type(mudfuzzer_event) is MF.SentBuffer ):
        control = app.sent_text
        text = mudfuzzer_event.b.decode ( encoding="utf-8", errors="replace" )
        app.sent_text.display_text ( text )
        app.invalidate ()

