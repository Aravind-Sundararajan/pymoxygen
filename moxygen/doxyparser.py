import os
import xml.etree.ElementTree as ET
import re
from functools import reduce
from itertools import chain
from moxygen.compound import Compound

class DoxygenParser:
    def __init__(self):
        self.references = {}
        self.root = Compound()

    def to_markdown(self, element, context=None):
        s = ''
        context = context or []
        if isinstance(element, str):
            s = element
        elif isinstance(element, dict):
            element_name = element.get('#name', '')
            if isinstance(element_name, list):
                element_name = element_name[0]

            if element_name == 'ref':
                s += self.ref_link(self.to_markdown(element['$$']), element['$']['refid'])
            elif element_name == '__text__':
                s = element['_']
            elif element_name in ('emphasis', 'bold', 'parametername', 'computeroutput'):
                s = '*' if element_name == 'emphasis' else '**' if element_name == 'bold' else '`'
            elif element_name == 'parameterlist':
                if element['$']['kind'] == 'exception':
                    s = '\n#### Exceptions\n'
                else:
                    s = '\n#### Parameters\n'
            elif element_name == 'parameteritem':
                s = '* '
            elif element_name == 'programlisting':
                s = '\n```cpp\n'
            elif element_name == 'orderedlist':
                context.append(element)
                s = '\n\n'
            elif element_name == 'itemizedlist':
                s = '\n\n'
            elif element_name == 'listitem':
                s = '1. ' if context and context[-1].get('#name') == 'orderedlist' else '* '
            elif element_name == 'sp':
                s = ' '
            elif element_name == 'heading':
                s = '## '
            elif element_name == 'xrefsect':
                s += '\n> '
            elif element_name == 'simplesect':
                if element['$']['kind'] == 'attention':
                    s = '> '
                elif element['$']['kind'] == 'return':
                    s = '\n#### Returns\n'
                elif element['$']['kind'] == 'see':
                    s = '**See also**: '
                else:
                    print(element['$']['kind'] + ' not supported.')
            elif element_name == 'formula':
                s = self.trim(element['_'])
                if s.startswith('$') and s.endswith('$'):
                    return s
                if s.startswith('\\[') and s.endswith('\\]'):
                    s = self.trim(s[2:-2])
                return '\n$$\n' + s + '\n$$\n'
            elif element_name == 'preformatted':
                s = '\n<pre>'
            elif element_name.startswith('sect'):
                context.append(element)
                s = '\n' + self.get_anchor(element['$']['id']) + '\n'
            elif element_name == 'title':
                level = '#' * int(context[-1]['#name'][-1])
                s = '\n{} {} {}\n'.format('#', level, element['_'])
            elif element_name == 'mdash':
                s = '&mdash;'
            elif element_name == 'ndash':
                s = '&ndash;'
            elif element_name == 'linebreak':
                s = '<br/>'
            elif element_name in ('xreftitle', 'entry', 'row', 'ulink', 'codeline', 'highlight', 'table', 'para', 
                                  'parameterdescription', 'parameternamelist', 'xrefdescription', 'verbatim', 'hruler', None):
                pass
            else:
                print(element_name + ': not yet supported.')

            if element.get('$$'):
                s += self.to_markdown(element['$$'], context)

            if element_name in ('parameterlist', 'para'):
                s += '\n\n'
            elif element_name == 'emphasis':
                s += '*'
            elif element_name == 'bold':
                s += '**'
            elif element_name == 'parameteritem':
                s += '\n'
            elif element_name == 'computeroutput':
                s += '`'
            elif element_name == 'parametername':
                s += '` '
            elif element_name == 'entry':
                s = self.escape_cell(s) + '|'
            elif element_name == 'programlisting':
                s += '```\n'
            elif element_name == 'codeline':
                s += '\n'
            elif element_name == 'ulink':
                s = self.link(s, element['$']['url'])
            elif element_name == 'orderedlist':
                context.pop()
                s += '\n'
            elif element_name == 'itemizedlist':
                s += '\n'
            elif element_name == 'listitem':
                s += '\n'
            elif element_name == 'entry':
                s = ' | '
            elif element_name == 'xreftitle':
                s += ': '
            elif element_name == 'preformatted':
                s += '</pre>\n'
            elif element_name.startswith('sect'):
                context.pop()
                s += '\n'
            elif element_name == 'row':
                s = '\n' + self.escape_row(s)
                if element.get('$$') and element['$$'][0]['$']['thead'] == 'yes':
                    for i, th in enumerate(element['$$']):
                        s += ('\n' + ' | '.join(['---------'] if i > 0 else ['', '---------']))[0]
            elif element_name == 'compounddef':
                pass
            else:
                print(element_name + ': not yet supported.')

        return s

    def ref_link(self, text, refid):
        return self.link(text, '{{#ref {} #}}'.format(refid))

    def link(self, text, href):
        return '[{}]({})'.format(text, href)

    def escape_row(self, text):
        return re.sub(r'\s*\|\s*$', '', text)

    def escape_cell(self, text):
        return (re.sub(r'^[\n]+|[\n]+$', '', text)  # Trim CRLF
                .replace(r'\|', '|')  # Unescape the pipe
                .replace('\n', '<br/>'))  # Escape CRLF

    def get_anchor(self, id):
        return id

    def trim(self, text):
        return re.sub(r'^[\s\t\r\n]+|[\s\t\r\n]+$', '', text)

    def copy(self, dest, prop, def_val):
        if prop in def_val.keys():
            dest.__setattr__(prop, self.trim(self.to_markdown(def_val.get(prop))))
        else:
            try:
                dest[prop] = self.trim(self.to_markdown(""))
            except Exception:
                dest.__setattr__(prop, self.trim(self.to_markdown("")))

    def summary(self, dest, def_val):
        summary = self.trim(self.to_markdown(def_val.get('briefdescription', '')))
        if not summary:
            summary = self.trim(self.to_markdown(def_val.get('detaileddescription', '')))
            if summary:
                first_sentence = summary.split('\n', 1)[0]
                if first_sentence:
                    summary = first_sentence
        try:
            dest.__setattr__('summary', summary)
        except Exception:
            dest['summary'] =  summary

    def parse_members(self, compound, props, members_def):
        for prop in list(props.keys()):
            compound.__setattr__(prop, props[prop])

        self.references[compound.refid] = compound
        if members_def:
            for member_def in members_def:
                member = {'refid': member_def.get("refid"), 'parent': compound}
                compound.members.append(member)
                for prop in member_def.attrib:
                    member[prop] = member_def.attrib[prop]
                self.references[member["refid"]] = member

    def parse_member(self, member, section, member_def):
        print('Processing member {} {}'.format(member['kind'], member['refid']))
        member['section'] = section
        self.copy(member, 'briefdescription', member_def)
        self.copy(member, 'detaileddescription', member_def)
        self.summary(member, member_def)

        m = []
        member_kind = member['kind']
        if member_kind in ('signal', 'slot'):
            m.extend(['{', member_kind, '} '])

        if member_kind == 'function':
            m.extend([member_def.attrib['prot'], ' '])  # public, private, ...
            if member_def.find('templateparamlist'):
                m.append('template<')
                template_params = member_def.find('templateparamlist').findall('param')
                m.extend([', ' + self.to_markdown(param.find('type')) + ' ' + self.to_markdown(param.find('declname'))
                          for param in template_params[1:]])
                m.append('>')
                m.append('  \n')

            m.extend(['inline ', ' ']) if member_def.attrib.get('inline') == 'yes' else m
            m.extend(['static ', ' ']) if member_def.attrib.get('static') == 'yes' else m
            m.extend(['virtual ', ' ']) if member_def.attrib.get('virt') == 'virtual' else m
            m.extend([self.to_markdown(member_def.find('type')), ' '])
            m.extend([member_def.attrib.get('explicit'), ' '] if member_def.attrib.get('explicit') else [])
            m.extend([self.ref_link(member['refid'], member['refid']), '('])

            if member_def.find('param'):
                params = member_def.findall('param')
                m.extend([', ' + self.to_markdown(param.find('type')) + ' ' + self.to_markdown(param.find('declname'))
                          for param in params[1:]])
            m.append(')')
            m.extend([' ', 'const']) if member_def.attrib.get('const') == 'yes' else m
            m.extend([' ', 'noexcept']) if member_def.find('argsstring').text.endswith('noexcept') else m
            m.extend([' = delete']) if member_def.find('argsstring').text.endswith('= delete') else m
            m.extend([' = default']) if member_def.find('argsstring').text.endswith('= default') else m

        elif member_kind == 'variable':
            m.extend([member_def.attrib['prot'], ' '])  # public, private, ...
            m.extend(['static ', ' ']) if member_def.attrib.get('static') == 'yes' else m
            m.extend(['mutable ', ' ']) if member_def.attrib.get('mutable') == 'yes' else m
            m.extend([self.to_markdown(member_def.find('type')), ' '])
            m.extend([self.ref_link(member['name'], member['refid'])])

        elif member_kind == 'property':
            m.extend(['{', member_kind, '} '])
            m.extend([self.to_markdown(member_def.find('type')), ' '])
            m.extend([self.ref_link(member['name'], member['refid'])])

        elif member_kind == 'enum':
            member['enumvalue'] = []
            for enum_value in member_def.findall('enumvalue'):
                enum_value_item = {}
                self.copy(enum_value_item, 'name', enum_value)
                self.copy(enum_value_item, 'briefdescription', enum_value)
                self.copy(enum_value_item, 'detaileddescription', enum_value)
                self.summary(enum_value_item, enum_value)
                member['enumvalue'].append(enum_value_item)

            m.extend([member_kind, ' ', self.ref_link(member['name'], member['refid'])])

        else:
            m.extend([member_kind, ' ', self.ref_link(member['name'], member['refid'])])

        member['proto'] = self.inline(m)

    def assign_to_namespace(self, compound, child):
        if compound.name != child['namespace']:
            print('namespace mismatch:', compound.name, '!=', child['namespace'])
        if child['parent']:
            del child['parent']['compounds'][child['id']]
        compound.compounds[child['id']] = child
        child['parent'] = compound

    def assign_namespace_to_group(self, compound, child):
        compound.compounds[child['id']] = child
        for id in child['compounds']:
            if id in compound.compounds:
                del compound.compounds[id]

    def assign_class_to_group(self, compound, child):
        compound.compounds[child['id']] = child
        child['groupid'] = compound.id
        child['groupname'] = compound.name

        for member in child['members']:
            member['groupid'] = compound.id
            member['groupname'] = compound.name

    def extract_page_sections(self, page, elements):
        for element in elements:
            if element['#name'] in ('sect1', 'sect2', 'sect3'):
                member = {'section': element['#name'], 'id': element['$']['id'], 'name': element['$']['id'], 'refid': element['$']['id'], 'parent': page}
                page['members'].append(member)
                self.references[member['refid']] = member

            if element.get('$$'):
                self.extract_page_sections(page, element['$$'])

    def parse_compound(self, compound, compound_def):
        print("compound def props:")
        for prop in compound_def.attrib:
            print(prop + " : " + compound_def.attrib[prop])
            compound.__setattr__(prop,compound_def.attrib[prop])
        #compound.__setattr__('kind', compound_def.find('kind').strip())
        #compound.__setattr__('fullname', compound_def.find('compoundname').text.strip())
        self.copy(compound, 'briefdescription', compound_def)
        self.copy(compound, 'detaileddescription', compound_def)
        self.summary(compound, compound_def)

        if compound_def.find('basecompoundref'):
            for basecompoundref in compound_def.findall('basecompoundref'):
                compound.basecompoundref.append({'prot': basecompoundref.attrib['prot'], 'name': basecompoundref.text.strip()})

        if compound_def.find('sectiondef'):
            for section in compound_def.findall('sectiondef'):
                members_def = section.findall('memberdef')
                if members_def:
                    for member_def in members_def:
                        member = self.references[member_def.attrib['id']]
                        if compound.kind == 'group':
                            member['groupid'] = compound.id
                            member['groupname'] = compound.name
                        elif compound.kind == 'file':
                            self.root['members'].append(member)

                        self.parse_member(member, section.attrib['kind'], member_def)

        compound.__setattr__('proto', self.inline([compound.kind, ' ', self.ref_link(compound.name, compound.refid)]))

        # kind specific parsing
        if compound.kind in ('class', 'struct', 'union', 'typedef'):
            namespace_ref = compound.name.split('::')
            compound.namespace = '::'.join(namespace_ref[:-1])

        elif compound.kind == 'file':
            pass

        elif compound.kind == 'page':
            self.extract_page_sections(compound, compound_def.findall('.//sect1|.//sect2|.//sect3'))

        elif compound.kind in ('namespace', 'group'):
            if compound.kind == 'group':
                compound.groupid = compound.id
                compound.groupname = compound.name

            if compound_def.find('innerclass'):
                for innerclass_def in compound_def.findall('innerclass'):
                    if compound.kind == 'namespace':
                        self.assign_to_namespace(compound, self.references[innerclass_def.attrib['refid']])
                    elif compound.kind == 'group':
                        self.assign_class_to_group(compound, self.references[innerclass_def.attrib['refid']])

            if compound_def.find('innernamespace'):
                compound.innernamespaces = []
                for namespace_def in compound_def.findall('innernamespace'):
                    self.assign_namespace_to_group(compound, self.references[namespace_def.attrib['refid']])

    def parse_index(self, root, index, options):
        for element in index:
            compound = root.find(element.attrib['refid'], element.find('name').text, True)
            self.parse_members(compound, element.attrib, element.findall('member'))
            if compound.kind != 'file':
                print('Parsing', os.path.join(options['directory'], compound.refid + '.xml'))
                doxygen = ET.parse(os.path.join(options['directory'], compound.refid + '.xml'))
                self.parse_compound(compound, doxygen.find('//compounddef'))

    def load_index(self, options, callback):
        err = None
        try:
            with open(os.path.join(options['directory'], 'index.xml'), 'r', encoding='utf-8') as file:
                data = file.read()
        except IOError as err:
            callback('Failed to load doxygen XML: ' + str(err))
            return

        try:
            xml_parser = ET.fromstring(data)
        except ET.ParseError as err:
            callback('Failed to parse doxygen XML: ' + str(err))
            return

        self.parse_index(self.root, xml_parser.findall('compound'), options)
        callback(err, self.root)

    def inline(self, strings):
        return re.sub(r'\n+', '', ' '.join(strings))


if __name__ == "__main__":
    c = Compound()