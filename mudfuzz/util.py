import re

def strip_ansi ( text ):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def snake_to_camel_case ( text ):
    return "".join([x.title() for x in text.split("_")])


