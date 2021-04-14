from prompt_toolkit import Application
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

def start_ui ( config_data, mudfuzzer ):

    root_container = VSplit([
        Window(content=FormattedTextControl(text='Hello world')),
        Window(width=1, char='|'),
        Window(content=FormattedTextControl(text='Hello world'))
    ])

    layout = Layout ( root_container )

    kb = KeyBindings ()

    @kb.add('c-c')
    def _(event):
        event,app.exit ()

    app = Application ( full_screen=True, layout=layout, key_bindings=kb )

    app.run ()

