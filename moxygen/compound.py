from moxygen.logger import getLogger

from functools import reduce
from itertools import chain

class Compound:
    def __init__(self, parent=None, id='', name=''):
        self.parent = parent
        self.kind = "dir"
        self.id = id
        self.name = name
        self.compounds = {}
        self.members = []
        self.basecompoundref = []
        self.filtered = {}

    def find(self, id, name, create=False):
        compound = self.compounds.get(id)
        if not compound and create:
            compound = Compound(self, id, name)
            self.compounds[id] = compound
        return compound

    def to_array(self, type='compounds', kind=None):
        arr = list(self.compounds.values()) if type == 'compounds' else self.members

        if kind:
            arr = [compound for compound in arr if not kind or compound.kind == kind]
        all_arr = []
        for compound in arr:
            this_arr = compound.to_array(type, kind)
            all_arr = all_arr + this_arr
        return list(chain(all_arr))

    def to_filtered_array(self, type='compounds'):
        all_arr = [item.to_filtered_array(type) for item in self.filtered.get(type, [])]
        return list(chain(all_arr))

    def filter_children(self, filters, groupid):
        member_filter = ""
        compound_filter = ""

        if filters is not None:
            member_filter = filters['members']
            compound_filter = filters['compound']

        for compound in self.to_array('compounds'):
            compound.filtered['members'] = compound.filter(compound.members, 'section', member_filter, groupid)
            compound.filtered['compounds'] = compound.filter(compound.compounds, 'kind', compound_filter, groupid)

        self.filtered['members'] = self.filter(self.members, 'section',  member_filter, groupid)
        self.filtered['compounds'] = self.filter(self.compounds, 'kind', compound_filter, groupid)

    def filter(self, collection, key, filters, groupid):
        categories = {}
        result = []
        if collection:
            for name, item in collection.items():
                if item:
                    if item.kind == 'namespace' and 'compounds' not in item.filtered and 'members' not in item.filtered:
                        continue


                    if groupid and item.groupid != groupid:
                        continue
                    categories.setdefault(item.__getattribute__(key), []).append(item)

            for category in filters:
                result += categories.get(category, [])

        return result