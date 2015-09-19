# -*- coding: utf-8 -*-

from trytond.pyson import Eval, Not, PYSONEncoder, In
from trytond.model import ModelView, ModelSQL, fields

from .tryton_utils import make_selection_display

from .du import JAMAICA_ID

INVISIBLEJM = {'invisible':In(Eval('country'), [JAMAICA_ID])}
VISIBLEJM = {'invisible':Not(In(Eval('country'), [JAMAICA_ID]))}

ADDRESS_STATES = {'readonly': ~Eval('active')}
ADDRESS_DEPENDS = ['active']

class PartyAddress(ModelSQL, ModelView):
    'Party Address'
    __name__ = 'party.address'

    streetbis = fields.Char('Apartment/Suite #', states=ADDRESS_STATES,
        depends=ADDRESS_DEPENDS)
    subdivision = fields.Many2One("country.subdivision",
            'Parish/Province', domain=[('country', '=', Eval('country'))],
            states=ADDRESS_STATES, depends=['active', 'country'])
    address_street_num = fields.Char('Street Number', size=8,
        states=ADDRESS_STATES)
    post_office = fields.Many2One(
        'country.post_office', 'Post Office (JM)',
        help="Closest Post Office, Jamaica only",
        domain=[('subdivision', '=', Eval('subdivision'))],
        depends=['subdivision'],
        states=VISIBLEJM)
    district_community = fields.Many2One(
        'country.district_community', 'District (JM)', states=VISIBLEJM,
        domain=[('post_office', '=', Eval('post_office'))],
        depends=['post_office'], help="Select District/Community, Jamaica only")
    desc = fields.Char('Additional Description', states=ADDRESS_STATES,
        help="Landmark or additional directions")
    simple_address = fields.Function(fields.Text('Simple Address'),
            'get_full_address')
    relationship_display = fields.Function(fields.Char('Relationship'),
                                           'get_relationship_display')

    @classmethod
    def __setup__(cls):
        super(PartyAddress, cls).__setup__()

        cls.streetbis.string = 'Apartment/Suite #'
        cls.subdivision.string = 'Parish/Province'

        origstate = {} if not cls.city.states else cls.city.states
        origstate.update(INVISIBLEJM)
        cls.city.states = origstate
        cls.zip.states = origstate

        cls.relationship = fields.Selection(
            [('', ''),
            ('offspring', 'Son/Daughter'),
            ('spouse','Spouse (husband/wife)'),
            ('parent','Parent (mother/father)'),
            ('guardian','Guardian/Foster parent'),
            ('sibling', 'Sibling (brother/sister)'),
            ('grandparent','Grandparent'),
            ('grandchild', 'Grandchild'),
            ('cousin','Cousin'),
            ('auntuncle','Aunt/Uncle'),
            ('girlboyfriend', 'Girlfriend/Boyfriend'),
            ('friend','Friend'),
            ('coworker','Co-worker'),
            ('other', 'Other')],
            'Relationship',
            help = 'Relationship of contact to patient')

    @classmethod
    def default_country(cls):
        return JAMAICA_ID

    def get_full_address(self, name):
        if self.country and self.country.id == JAMAICA_ID:
            addr, line = [], []
            if self.address_street_num: line.append(self.address_street_num)
            if self.street: line.append(','.join([self.street, '']))
            if self.streetbis: line.extend([' Apt#', self.streetbis])
            if line:
                addr.append(u' '.join(line[:]))
                line = []
            if self.district_community and self.district_community.id:
                line.append(','.join([self.district_community.name, '']))

            if self.post_office:
                line.append(self.post_office.name)

            if line:
                addr.append(u' '.join(line[:]))
                line = []

            if name == 'simple_address' :
                return '\n'.join(addr)

            if self.subdivision:
                # if not self.district_community and self.district
                line.append(self.subdivision.name)

            # line.append(self.country.name)

            addr.append(u' '.join(line))
            return (u'\r\n').join(addr)
        else:
            return super(PartyAddress, self).get_full_address(name)

    def get_relationship_display(self, name):
        return make_selection_display()(self, 'relationship')
