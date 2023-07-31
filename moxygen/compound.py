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

    def to_array(self, type_='compounds', kind=None):
        if type_ == 'compounds':
            arr = list(self.compounds.values())
        else:
            arr = self.members

        if kind:
            arr = [compound for compound in arr if compound.kind == kind]

        all_arr = []
        for compound in arr:
            this_arr = compound.to_array(type_, kind)
            all_arr.append(this_arr)

        if not all_arr:  # Base case: No members, return itself as a single-element list.
            return [self]

        return list(chain.from_iterable(all_arr))

    def to_filtered_array(self, type_='compounds'):
        all_arr = []
        if type_ in self.filtered:
            all_arr = [item.to_filtered_array(type_) for item in self.filtered[type_]]
            if all_arr == []:
                all_arr = all_arr.append(self)
        print("ALL ARR")
        print(all_arr)
        flattened_arr = list(chain.from_iterable(all_arr))
        return flattened_arr

    def filter_children(self, filters, groupid=None):
        member_filter = {}
        compound_filter = {}

        if filters is not None:
            member_filter = filters['members']
            compound_filter = filters['compounds']
        compounds = self.to_array()
        for compound in compounds:
            compound.filtered['members'] = compound.filter(compound.members, 'section', member_filter, groupid)
            compound.filtered['compounds'] = compound.filter(compound.compounds, 'kind', compound_filter, groupid)

        self.filtered['members'] = self.filter(self.members, 'section',  member_filter, groupid)
        self.filtered['compounds'] = self.filter(self.compounds, 'kind', compound_filter, groupid)

    def filter(self, collections, key, filters, groupid=None):
        categories = {}
        result = []
        if type(collections) == list:
            for item in collections:
                if item['kind'] == 'namespace' and 'compounds' not in item['filtered'] and 'members' not in item['filtered']:
                    continue

                if groupid and item[groupid] != groupid:
                    continue
                if key in list(item.keys()):
                    if item[key] not in categories:
                        categories[item[key]] = []

                    categories[item[key]].append(item)
        elif type(collections) == dict:
            for name, item in collections.items():
                if item:
                    if item.kind == 'namespace' and 'compounds' not in item.filtered and 'members' not in item.filtered:
                        continue

                    if groupid and item.groupid != groupid:
                        continue

                    if item.__getattribute__(key) not in categories:
                        categories[item.__getattribute__(key)] = []

                    categories[item.__getattribute__(key)].append(item)

        for category in filters:
            result += categories.get(category, [])
        return result
