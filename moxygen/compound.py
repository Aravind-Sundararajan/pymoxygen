from moxygen.logger import getLogger

class Compound:
    def __init__(self, parent, id, name):
        self.parent = parent
        self.id = id
        self.name = name
        self.compounds = {}
        self.members = []
        self.basecompoundref = []
        self.filtered = {}

    def __setitem__(self, value):
            """operator overload [] assignment"""
            self.compounds[value] = value
            return 0

    def find(self, id, name, create):
        compound = self.compounds.get(id)

        if not compound and create:
            compound = Compound(self, id, name)
            self.compounds[id] = compound

        return compound

    def to_array(self, type='compounds', kind=None):
        arr = list(self.compounds.values()) if type == 'compounds' else self.members

        if type == 'compounds':
            all_items = []
            for compound in arr:
                if not kind or compound.kind == kind:
                    all_items.append(compound)
                    all_items.extend(compound.to_array(type, kind))
            arr = all_items

        return arr

    def to_filtered_array(self, type='compounds'):
        all_items = []
        for item in self.filtered.get(type, []):
            children = item.to_filtered_array(type)
            all_items.append(item)
            all_items.extend(children)
        return all_items

    def filter_children(self, filters, groupid):
        for compound in self.to_array('compounds'):
            compound.filtered['members'] = compound.filter(compound.members, 'section', filters['members'], groupid)
            compound.filtered['compounds'] = compound.filter(compound.compounds, 'kind', filters['compounds'], groupid)
        self.filtered['members'] = self.filter(self.members, 'section', filters['members'], groupid)
        self.filtered['compounds'] = self.filter(self.compounds, 'kind', filters['compounds'], groupid)

    def filter(self, collection, key, filter_list, groupid):
        categories = {}
        result = []

        for item in collection.values():
            if item:

                # Skip empty namespaces
                if item.kind == 'namespace':
                    if not item.filtered.get('compounds') and not item.filtered.get('members'):
                        continue

                # Skip items not belonging to the current group
                elif groupid and item.groupid != groupid:
                    continue

                categories.setdefault(item[key], []).append(item)

        for category in filter_list:
            result.extend(categories.get(category, []))

        return result
