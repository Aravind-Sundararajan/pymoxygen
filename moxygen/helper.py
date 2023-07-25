import os
import re
import python_utils as util
from moxygen.logger import getLogger

def inline(code):
    if isinstance(code, list):
        s = ''
        is_inline = False
        for e in code:
            refs = re.split(r"(\[.*\]\(.*\)|\n|\s{2}\n)", e)    
            for f in refs:
                if f.startswith('['):
                    # link
                    link = re.match(r"\[(.*)\]\((.*)\)", f)
                    if link:
                        if is_inline:
                            s += '`'
                            is_inline = False
                        s += '[`{}`]({})'.format(link.group(1), link.group(2))
                elif f == '\n' or f == '  \n':
                    # line break
                    if is_inline:
                        s += '`'
                        is_inline = False
                    s += f
                elif f:
                    if not is_inline:
                        s += '`'
                        is_inline = True
                    s += f
        return s + ('`' if is_inline else '')
    else:
        return '`{}`'.format(code)

def get_anchor(name, options):
    if options['anchors']:
        return '{{#{}{}}}'.format(name, '}')
    elif options['htmlAnchors']:
        return '<a id="{}"></a>'.format(name)
    else:
        return ''

def find_parent(compound, kinds):
    while compound:
        if compound['kind'] in kinds:
            return compound
        compound = compound['parent']

def resolve_refs(content, compound, references, options):
    import re
    return re.sub(r"\{#ref ([^ ]+) #\}", lambda m: 
                  '#' + m.group(1) if m.group(1) in references else 
                  '{}#{}'.format(compound_path(find_parent(references[m.group(1)], ['page']), options), m.group(1)) 
                  if find_parent(references[m.group(1)], ['page']) and options['groups'] else 
                  '{}#{}'.format(compound_path(references[m.group(1)], options), m.group(1)) if options['groups'] else 
                  compound_path(find_parent(references[m.group(1)], ['namespace', 'class', 'struct']), options) + '#' + m.group(1),
                  content)

def compound_path(compound, options):
    if compound['kind'] == 'page':
        return os.path.dirname(options['output']) + "/page-" + compound['name'] + ".md"
    elif options['groups']:
        return util.format(options['output'], compound['groupname'])
    elif options['classes']:
        return util.format(options['output'], compound['name'].replace(':', '-').replace('<', '(').replace('>', ')'))
    else:
        return options['output']

def write_compound(compound, contents, references, options):
    for content in contents:
        resolve_content = resolve_refs(content, compound, references, options)
        if resolve_content:
            write_file(compound_path(compound, options), resolve_content)

def write_file(filepath, contents):
    logger = getLogger()
    logger.verbose('Writing: ' + filepath)
    with open(filepath, 'w') as f:
        f.write(''.join(contents))
