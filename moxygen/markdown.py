import re

def ref_link(text, refid):
    return link(text, '{{#ref {} #}}'.format(refid))

def link(text, href):
    return '[{}]({})'.format(text, href)

def escape_row(text):
    return text.replace(r'\s*\|\s*$', '')

def escape_cell(text):
    return (text
            .replace(r'^[\n]+|[\n]+$', '')  # Trim CRLF
            .replace(r'\|', r'\|')          # Escape the pipe
            .replace(r'\n', '<br/>'))       # Escape CRLF

escape = {
    'row': escape_row,
    'cell': escape_cell
}
