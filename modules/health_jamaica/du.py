# -*- coding: utf-8 -*-

from datetime import datetime
import hashlib
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal, And, Or, In
from trytond.pool import Pool

_Jamaica_instance = False

def JAMAICA():
    global _Jamaica_instance
    if not _Jamaica_instance:
        _Jamaica_instance, = Pool().get('country.country').search([('code','=',
                                                                 'JM')])
    return _Jamaica_instance

JAMAICA_ID = 89

INVISIBLEJM = {'invisible':In(Eval('address_country'), [JAMAICA_ID])}
VISIBLEJM = {'invisible':Not(In(Eval('address_country'), [JAMAICA_ID]))}


class DomiciliaryUnit(ModelSQL, ModelView):
    'Domiciliary Unit'
    __name__ = 'gnuhealth.du'

    address_street_num = fields.Char('Street Number', size=8)
    address_post_office = fields.Many2One(
        'country.post_office', 'Post Office (JM)',
        help="Closest Post Office, Jamaica only",
        domain=[('subdivision', '=', Eval('address_subdivision'))],
        depends=['address_subdivision'],
        states=VISIBLEJM)
    address_district_community = fields.Many2One(
        'country.district_community', 'District (JM)',
        domain=[('post_office', '=', Eval('address_post_office'))],
        depends=['address_post_office'],
        help="Select District/Community, Jamaica only",
        states=VISIBLEJM)
    city_town = fields.Function(fields.Char('City/Town/P.O.'), 'get_city_town')

    full_address = fields.Function(fields.Text('Full Address'),
            'get_full_address')
    simple_address = fields.Function(fields.Text('Address'),
                                     'get_full_address')

    @classmethod
    def __setup__(cls):
        super(DomiciliaryUnit, cls).__setup__()

        cls.name.required = False
        cls.name.readonly = True
        cls.desc.string = 'Additional Directions'
        cls.desc.help = 'Landmark or descriptions to help identify the home'
        cls.address_subdivision.string = 'Parish/Province'
        cls.address_subdivision.help = "Select Parish, State or Province"

        cls.address_district.states = INVISIBLEJM
        cls.address_municipality.states = INVISIBLEJM
        cls.address_city.states = INVISIBLEJM
        cls.address_zip.states = INVISIBLEJM

        cls.dwelling.selection = [
            (None, ''),
            ('single_house', 'Single / Detached House'),
            ('apartment', 'Apartment'),
            ('townhouse', 'Townhouse'),
            ('factory', 'Factory'),
            ('building', 'Building'),
            ('mobilehome', 'Mobile Home'),
        ]
        cls.roof_type.selection = [
            (None, ''),
            ('concrete', 'Concrete/Slab'),
            ('alusteel', 'Steel/Aluminium/Zinc'),
            ('wood', 'Wood'),
            ('mud', 'Mud'),
            ('thatch', 'Thatched'),
            ('stone', 'Stone'),
            ('shingles', 'Wooden or other non-clay shingles'),
            ('clay', 'Clay shingles'),
        ]


    @classmethod
    def default_address_country(cls):
        return JAMAICA().id

    def get_city_town(self, name):
        '''returns the post office for jamaica or the city or municipality for
        other addresses'''

        if self.address_country == JAMAICA() and self.address_post_office:
            return self.address_post_office.name
        else:
            return self.address_city or self.address_municipality

    def get_full_address(self, name):
        if self.address_country:
            addr,line = [],[]
            if self.address_street_num: line.append(self.address_street_num)
            if self.address_street: line.append(','.join([self.address_street,'']))
            if self.address_street_bis: line.extend([' Apt#', self.address_street_bis])
            if line:
                addr.append(u' '.join(line[:]))
                line =[]
            if self.address_country.id == JAMAICA().id :
                if self.address_district_community and self.address_district_community.id:
                    line.append(','.join([self.address_district_community.name,'']))

                if self.address_post_office:
                    line.append(self.address_post_office.name)

                if line:
                    addr.append(u' '.join(line[:]))
                    line=[]
            if name == 'simple_address': # stop now. Don't attach subdiv + country
                return '\n'.join(addr)

            if self.address_subdivision:
                # if not self.district_community and self.district
                line.append(self.address_subdivision.name)
            line.append(self.address_country.name)

            addr.append(u' '.join(line))
            return (u'\r\n').join(addr)


    @classmethod
    def generate_du_code(cls, prefix, *args):
        ''' generates domunit code as follows :
        PARISHCODE-{RANDOM_HEX_DIGITSx8}.
        The parish code is taken directly from the parish when selected or 
        when a post office is selected. The RANDOM_HEX_DIGITSx8 is the
        first 8 chars from the SHA1 hash of [self.desc, self.post_office.code,
                    self.address_district_community.name,
                    self.address_street, self.address_street_num,
                    self.address_street_bis]) #, str(time.time())])
        separated by semi-colon (;)
        '''
        codelist = [prefix]

        hashlist = map(lambda x: str(x), filter(None, args))
        codelist.append(hashlib.sha1(';'.join(hashlist)).hexdigest()[:8])

        return '-'.join(codelist)

    @classmethod
    def create(cls, vlist):
        
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not 'name' in values:
                state_code = values.get('address_subdivision')
                if state_code:
                    state_code = (Pool().get('country.subdivision')(state_code)).code
                values['name'] = cls.generate_du_code(state_code, datetime.now(),
                    *[values.get(r) for r in ('desc','address_post_office',
                                              'address_district_community',
                                              'address_street',
                                              'address_street_num',
                                              'address_street_bis')])
        return super(DomiciliaryUnit, cls).create(vlist)
