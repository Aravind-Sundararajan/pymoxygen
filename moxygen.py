import os
import argparse
from moxygen import helper, template
from moxygen.compound import Compound
from moxygen.doxyparser import DoxygenParser
from moxygen.template import Renderer
from moxygen.logger import initLogger

class Moxygen:
    def __init__(self):
        self.defaultOptions = {
            'directory': None,
            'output': 'api.md',
            'groups': False,
            'noindex': False,
            'anchors': True,
            'language': 'cpp',
            'template': 'templates',
            'pages': False,
            'classes': False,
            'output_s': 'api_%s.md',
            'logfile': 'pymoxygen.log',
            'filters': {
                'members': [
                    'define',
                    'enum',
                    # 'enumvalue',
                    'func',
                    # 'variable',
                    'property',
                    'public-attrib',
                    'public-func',
                    'protected-attrib',
                    'protected-func',
                    'signal',
                    'public-slot',
                    'protected-slot',
                    'public-type',
                    'private-attrib',
                    'private-func',
                    'private-slot',
                    'public-static-func',
                    'private-static-func',
                ],
                'compounds': [
                    'namespace',
                    'class',
                    'struct',
                    'union',
                    'typedef',
                    'interface',
                    # 'file',
                ]
            },
        }
        self.doxyparser = DoxygenParser()

    def run(self, options):
        initLogger(options, self.defaultOptions)
        r = Renderer()
        # Sanitize options
        if options['output'] is None:
            if options['classes'] or options['groups']:
                options['output'] = self.defaultOptions['output_s']
            else:
                options['output'] = self.defaultOptions['output']

        if (options['classes'] or options['groups']) and '%s' not in options['output']:
            raise ValueError("The `output` file parameter must contain an '%s' for group or class name " +
                             "substitution when `groups` or `classes` are enabled.")

        if options['templates'] is None:
            if options['language'] is not None:
                options['template'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.defaultOptions['template'], options['language'])
            else:
                options['template'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.defaultOptions['template'], self.defaultOptions['language'])
        
        if options['filters'] is None:
            options['filters'] = self.defaultOptions['filters']

        # Load template
        r.register_helper(options)
        r.load(options['template'])

        # Parse files
        def loadIndexCallback(err, root: Compound):
            if err:
                raise err
            # Output groups
            if options['groups']:
                groups = root.to_array('compounds', 'group')
                if not groups:
                    raise ValueError("You have enabled `groups` output, but no groups were " +
                                     "located in your doxygen XML files.")
                group: Compound
                for group in groups:
                    group.filter_children(options['filters'], group.id)
                    compounds = group.to_filtered_array('compounds')
                    compounds.insert(0, group)  # insert group at top
                    helper.write_compound(group, r.render_array(compounds), self.doxyparser.references, options)
            elif options['classes']:
                rootCompounds = root.to_array('compounds', 'namespace')
                if not rootCompounds:
                    raise ValueError("You have enabled `classes` output, but no classes were " +
                                     "located in your doxygen XML files.")
                
                comp: Compound
                e: Compound
                for comp in rootCompounds:
                    comp.filter_children(options['filters'])
                    compounds = comp.to_filtered_array()
                    helper.write_compound(comp, [r.render_array(compounds)], self.doxyparser.references, options)
                    for e in compounds:
                        e.filter_children(options['filters'])
                        compounds = e.to_filtered_array()
                        helper.write_compound(e, [r.render_array(compounds)], self.doxyparser.references, options)
            # Output single file
            else:
                root.filter_children(options['filters'])
                compounds = root.to_filtered_array('compounds')
                print("compounds:")
                print(compounds)
                if not options.get('noindex'):
                    compounds.insert(0, root)  # insert root at top if index is enabled
                contents = r.render_array(compounds)
                if contents is not None:
                    contents.append('Generated by [pymoxygen](https://github.com/Aravind-Sundararajan/pymoxygen)')
                else:
                    contents = ""
                helper.write_compound(root, contents, self.doxyparser.references, options)

            if options['pages']:
                pages = root.to_array('compounds', 'page')
                if not pages:
                    raise ValueError("You have enabled `pages` output, but no pages were " +
                                     "located in your doxygen XML files.")
                page: Compound
                for page in pages:
                    compounds = page.to_filtered_array('compounds')
                    compounds.insert(0, page)
                    helper.write_compound(page, r.render_array(compounds), self.doxyparser.references, options)

        self.doxyparser.load_index(options, loadIndexCallback)


def main():
    parser = argparse.ArgumentParser(description="Doxygen converter for xml to markdown")
    parser.add_argument('-V', '--version',                  help="output the version number")
    parser.add_argument('-d', '--directory',default="C:\\pymoxygen\\example\\xml",    help="output file, must contain ""%s"" when using `groups` or `classes`")
    parser.add_argument('-o', '--output',default="./doc/readme.md",    help="output file, must contain ""%s"" when using `groups` or `classes`")
    parser.add_argument('-g', '--groups',           help="output doxygen groups into separate files")
    parser.add_argument('-c', '--classes',          help="output doxygen classes into separate files")
    parser.add_argument('-p', '--pages',            help="output doxygen pages into separate files")
    parser.add_argument('-n', '--noindex',          help="disable generation of the index, ignored with `groups` or `classes`")
    parser.add_argument('-a', '--anchors',          help="add anchors to internal links")
    parser.add_argument('-H', '--html-anchors',     help="add html anchors to internal links")
    parser.add_argument('-l', '--language',         help="programming language")
    parser.add_argument('-t', '--templates',        help="custom templates directory")
    parser.add_argument('-L', '--logfile',          help="output log messages to file")
    parser.add_argument('-q', '--quiet',            help="quiet mode")
    parser.add_argument('-f', '--filters',            help="filters")
    args = parser.parse_args()
    options = vars(args)
    m = Moxygen()
    m.run(options)
    

if __name__ == '__main__':
    main()