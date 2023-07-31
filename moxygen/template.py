import os
import os.path as path
import pybars as handlebars

import moxygen.doxyparser as doxyparser
import moxygen.helper as helper
from moxygen.logger import getLogger


class Renderer:
    def __init__(self, options):
        # Loaded templates
        self.compiler = handlebars.Compiler()
        print(dir(self.compiler))
        self.templates = {}
        self.helpers = {}
        self.options = options

    # Load templates from the given directory
    def load(self, template_directory):
        for filename in os.listdir(template_directory):
            fullname = path.join(template_directory, filename)
            with open(fullname, 'r', encoding='utf-8') as file:
                template = self.compiler.compile(file.read()) #NoEscape=True, ,  strict=True
                self.templates[filename[:-3]] = template

    def render(self, compound):
        log = getLogger()
        template = None
        print("COMPOUND")
        print(compound)
        log.info(f'Rendering {compound.kind} {compound.name}')

        if compound.kind == 'index':
            template = 'index'
        elif compound.kind == 'page':
            template = 'page'
        elif compound.kind in ['group', 'namespace']:
            if len(compound.compounds) == 1 and \
               compound.compounds[next(iter(compound["compounds"]))]["kind"] == 'namespace':
                return None
            template = 'namespace'
        elif compound.kind in ['class', 'struct', 'interface']:
            template = 'class'
        else:
            log.warning(f'Cannot render {compound.kind} {compound.name}')
            log.warning(f'Skipping {compound}')
            return None

        if template not in self.templates:
            raise ValueError(f'Template "{template}" not found in your templates directory.')
        result = self.templates[template](compound, helpers=self.helpers)
        print(result)
        return result.replace(r'(\r\n|\r|\n){3,}', r'$1\n')

    def render_array(self, compounds):
        return [self.render(compound) for compound in compounds]

    # Register handlebars helper
    def register_helper(self, options):
        print(options)
        # Escape the code for a table cell.
        def cell(code, options, items):
            return code.replace('|', r'\|').replace('\n', '<br/>')
        self.helpers['cell']= cell
        #self.compiler._helpers['cell']=cell

        # Escape the code for titles.
        def title(code, options, items):
            return code.replace('\n', '<br/>')
        self.helpers['title']= title
        #self.compiler._helpers['title']=title

        # Generate an anchor for internal links
        def anchor(name, options):
            return helper.get_anchor(name, options)
        self.helpers['anchor']= anchor
        #self.compiler._helpers['anchor']=anchor


if __name__ == "__main__":
    r = Renderer()
    options = {}
