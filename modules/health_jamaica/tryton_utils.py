'''Utilities that make dealing with tryton idosynchrasies easier'''

def negate(operator):
    '''returns the opposite operator of a domain operator. 
    e.g. if called as negate('=') it will return "!="
    '''
    converter = {u'=':u'!=', u'<':u'>', u'<=':u'>='}
    converter.update([(y,x) for x,y in converter.items()])
    return converter.get(operator, (u'not {}').format(operator))


def replace_clause_column(clause, new_column):
    '''replaces the column in a query clause. This is for clauses used
    with .search and .find methods ... domain language'''
    return (new_column, ) + tuple(clause[1:])

def negate_clause(clause):
    # ToDo: verify if this can work for all clause types
    return (clause[0], negate(clause[1]), clause[2])

def make_selection_display():
    def _get_x_display(self, field_name):
        fieldlist = getattr(self, '_fields')
        # import pdb; pdb.set_trace()
        field_selections = fieldlist[field_name].selection
        field_obj = getattr(self, field_name)
        xdict = dict(filter(lambda x: x[0], field_selections))
        return xdict.get(field_obj, '')

    return _get_x_display
