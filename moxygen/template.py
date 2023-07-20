import os
import logging
import os.path as path
import handlebars

import doxyparser
import helpers
import markdown

class Renderer:
    def __init__(self):
        # Loaded templates
        self.templates = {}

    # Load templates from the given directory
    def load(self, template_directory):
        for filename in os.listdir(template_directory):
            fullname = path.join(template_directory, filename)
            with open(fullname, 'r', encoding='utf-8') as file:
                template = handlebars.compile(file.read(), no_escape=True, strict=True)
                self.templates[filename[:-3]] = template

    def render(self, compound):
        log = logging.getLogger(__name__)
        template = None

        log.info(f'Rendering {compound["kind"]} {compound["fullname"]}')

        if compound["kind"] == 'index':
            template = 'index'
        elif compound["kind"] == 'page':
            template = 'page'
        elif compound["kind"] in ['group', 'namespace']:
            if len(compound["compounds"]) == 1 and \
               compound["compounds"][next(iter(compound["compounds"]))]["kind"] == 'namespace':
                return None
            template = 'namespace'
        elif compound["kind"] in ['class', 'struct', 'interface']:
            template = 'class'
        else:
            log.warning(f'Cannot render {compound["kind"]} {compound["fullname"]}')
            log.warning(f'Skipping {compound}')
            return None

        if template not in self.templates:
            raise ValueError(f'Template "{template}" not found in your templates directory.')

        result = self.templates[template](compound)
        return result.replace(r'(\r\n|\r|\n){3,}', r'$1\n')

    def render_array(self, compounds):
        return [self.render(compound) for compound in compounds]

    # Register handlebars helpers
    def register_helpers(self, options):
        # Escape the code for a table cell.
        def cell(code):
            return code.replace('|', r'\|').replace('\n', '<br/>')
        handlebars.register_helper('cell', cell)

        # Escape the code for titles.
        def title(code):
            return code.replace('\n', '<br/>')
        handlebars.register_helper('title', title)

        # Generate an anchor for internal links
        def anchor(name):
            return helpers.get_anchor(name, options)
        handlebars.register_helper('anchor', anchor)
