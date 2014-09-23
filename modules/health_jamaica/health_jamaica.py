# -*- coding: utf-8 -*-
##############################################################################
#
#    Health-Jamaica: The Jamaica Electronic Patient Administration System
#    Copyright 2014  Ministry of Health (NHIN), Jamaica <admin@mohnhin.info>
#
#    Based on GNU Health
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import string
import random
import hashlib
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['PartyPatient', 'PatientData', 'AlternativePersonID', 'PostOffice',
    'DistrictCommunity', 'DomiciliaryUnit', 'Newborn', 'Insurance',
    'PartyAddress', 'HealthProfessional']
__metaclass__ = PoolMeta

_STATES = {
    'invisible': Not(Bool(Eval('is_person'))),
}
_DEPENDS = ['is_person']

JAMAICA = lambda : Pool().get('country.country')(89)

class PartyPatient (ModelSQL, ModelView):
    'Party'
    __name__ = 'party.party'
    
    ref = fields.Char(
        'UPI',
        help='Universal Person Indentifier',
        states=_STATES, depends=_DEPENDS, readonly=True)
    name = fields.Char('Name', required=True, 
        states={'readonly':Bool(Eval('is_person'))},
        )
    alias = fields.Char('Alias', states=_STATES, depends=_DEPENDS,
        help="Nickname, pet-name or other name by which the patient is called")
    firstname = fields.Char('First name', states=_STATES, depends=_DEPENDS,
        select=True)
    middlename = fields.Char('Middle Name', states=_STATES, depends=_DEPENDS,
        help="Middle name or names of Patient")
    mother_maiden_name = fields.Char("Mother's Maiden Name", states=_STATES, 
        depends=_DEPENDS, help="Mother's Maiden Name")
    father_name = fields.Char("Father's Name", states=_STATES, depends=_DEPENDS,
        help="Father's Name")
    lastname = fields.Char('Last Name', help='Last Name',
        states={'invisible': Not(Bool(Eval('is_person')))},
        select=True)

    suffix = fields.Selection([
        (None,''),
        ('jr', 'Jr. - Junior'),
        ('sr', 'Sr. - Senior'),
        ('II', 'II - The Second'),
        ('III', 'III - The Third'),
        ], 'Suffix', states=_STATES, depends=_DEPENDS)

    marital_status = fields.Selection([
        (None, ''),
        ('s', 'Single'),
        ('m', 'Married'),
        ('c', 'Living with partner'),
        ('v', 'Visiting'),
        ('w', 'Widowed'),
        ('d', 'Divorced'),
        ('x', 'Separated'),
        ('n', 'Not Applicable'),
        ('u', 'Unknown'),
        ], 'Marital Status', sort=False)

    # gender vs sex: According to the AMA Manual of Style :
    # Gender refers to the psychological/societal aspects of being male or female,
    # sex refers specifically to the physical aspects. Do not interchange
    sex = fields.Selection([
        (None,''),
        ('m', 'Male'),
        ('f', 'Female'),
        ('u', 'Unknown')
        ], 'Sex', states={'required':Bool(Eval('is_person'))})

    party_warning_ack = fields.Boolean('Party verified', 
        states={
            'invisible': Not(Bool(Eval('unidentified'))),
            'readonly': Bool(Eval('ref'))
            })

    occupation = fields.Many2One('gnuhealth.occupation', 'Occupational Group')

    def get_rec_name(self, name):
        # simplified since we generate the person name and all others are okay
        return self.name

    @classmethod
    def __setup__(cls):
        super(PartyPatient, cls).__setup__()
        new_state = {'readonly': Bool(Eval('ref'))}
        if new_state.keys()[0] not in cls.unidentified.states:
            cls.unidentified.states.update(new_state)
        if 'unidentified' not in cls.unidentified.on_change:
            cls.unidentified.on_change.add('unidentified')
        cls._error_messages.update({
            'unidentified_party_warning':
            '== UNIDENTIFIED VERIFICATION ==\n\n'
            '- IS THE PARTY UNINDENTIFIED ? \n'
            'Verify and check mark the party as verified\n',
        })

    @staticmethod
    def default_party_warning_ack():
        return True

    def on_change_unidentified(self):
        party_warning_ack = True
        if self.unidentified:
            party_warning_ack = False
        return {
            'party_warning_ack': party_warning_ack,
        }

    @fields.depends('lastname', 'firstname', 'middlename')
    def on_change_with_name(self, *arg, **kwarg):
        namelist = [self.lastname]
        if self.firstname:
            namelist.extend([',', self.firstname])
        if self.middlename:
            namelist.append(self.middlename)
        return ' '.join(namelist)

    @classmethod
    def generate_upc(cls):
        # Add a default random string in the ref field.
        # The STRSIZE constant provides the length of the HIN
        # The format of the UPC is XXXNNNXXX
        STRSIZE = 9
        hin = ''
        for x in range(STRSIZE): 
            if ( x < 3 or x > 5 ):
                hin = hin + random.choice(string.ascii_uppercase)
            else:
                hin = hin + random.choice(string.digits)
        return hin

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('party.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not 'ref' in values:
                values['ref'] = cls.generate_upc()
                if 'unidentified' in values and values['unidentified']:
                    values['ref'] = 'NN-' + values.get('ref')
                if 'is_person' in values and not values['is_person']:
                    values['ref'] = 'NP-' + values['ref']
            if not values.get('code'):
                config = Configuration(1)
                # Use the company name . Initially, use the name
                # since the company hasn't been created yet.
                prefix = Transaction().context.get('company.rec_name') \
                    or values['name']
                values['code'] = str(prefix) + '-' + \
                    Sequence.get_id(config.party_sequence.id)

            values['code_length'] = len(values['code'])
            values.setdefault('addresses', None)
        return super(PartyPatient, cls).create(vlist)

    @classmethod
    def validate(cls, parties):
        super(PartyPatient, cls).validate(parties)
        for party in parties:
            party.check_party_warning()

    def check_party_warning(self):
        if not self.party_warning_ack:
            self.raise_user_error('unidentified_party_warning')

    # @classmethod
    # def write(cls, parties, vals):
    #     # We use this method overwrite to make the fields that have a unique
    #     # constraint get the NULL value at PostgreSQL level, and not the value
    #     # '' coming from the client
    #     print('parties and vals')
    #     print(repr(parties))
    #     print(repr(vals))

    #     # if vals.get('ref') == '':
    #     #     vals['ref'] = None
    #     return super(PartyPatient, cls).write(parties, vals)

class PatientData(ModelSQL, ModelView):
    '''Patient related information, redefined to fix name display/generation'''
    __name__ = 'gnuhealth.patient'

    ses = fields.Selection([
        (None, ''),
        ('0', 'Lower'),
        ('1', 'Lower-middle'),
        ('2', 'Middle'),
        ('3', 'Upper-middle'),
        ('4', 'Upper'),
        ], 'Socioeconomics', help="SES - Socioeconomic Status", sort=False)

    religion = fields.Selection([
        (None, ''),
        ('christianw', 'Christian (Traditional) - Anglican/Baptist/Catholic etc.'),
        ('sda', 'Seventh Day Adventists'),
        ('jehova', 'Jehova\'s Witness'),
        ('christmodern', 'Christian (Modern) - Universal/Mormon etc'),
        ('rasta','Rastafarian'),
        ('jew', 'Jewish (all)'),
        ('muslims', 'Islam (Muslim, all schools)'),
        ('buddhist', 'Buddhist'),
        ('hindu', 'Hindu'),
        ('none', 'None/Atheist/Agnostic'),
        ('unknown', 'Unknown')
        ], 'Religion', help='Religion or religious persuasion', sort=False)

    def get_rec_name(self, name):
        return self.name.name

    @classmethod
    def __setup__(cls):
        super(PatientData, cls).__setup__()
        cls.puid.string = 'UPI'

class PartyAddress(ModelSQL, ModelView):
    'Party Address, defines parties that are related to patients'
    __name__ = 'party.address'

    relationship = fields.Selection([
        (None, ''),
        ('spouse','Spouse (husband/wife)'),
        ('parent','Parent (mother/father)'),
        ('guardian','Guardian/Foster parent'),
        ('sibling', 'Sibling (brother/sister)'),
        ('grandparent','Grandparent'),
        ('cousin','Cousin'),
        ('auntuncle','Aunt/Uncle'),
        ('friend','Friend'),
        ('coworker','Co-worker'),
        ('other', 'Other')
        ],'Relationship', help="Relationship of contact to patient", sort=True)



class AlternativePersonID (ModelSQL, ModelView):
    'Alternative person ID'
    __name__ ='gnuhealth.person_alternative_identification' 
   
    issuing_institution = fields.Many2One('gnuhealth.institution', 'Issued By',
        help='Institution that assigned the medical record number',
        states={'required':Eval('alternative_id_type') == 'medical_record'})
    expiry_date = fields.Date('Expiry Date',
        states={'required':Eval('alternative_id_type') == 'passport'})

    @classmethod
    def __setup__(cls):
        super(AlternativePersonID, cls).__setup__()
        selections = [
                ('trn','TRN (Taxpayer Registration Number)'),
                ('medical_record', 'Medical Record Number'),
                ('pathID','PATH ID'),
                ('gojhcard','GOJ Health Card'),
                ('votersid','GOJ Voter\'s ID'),
                ('birthreg', 'Birth Registration ID'),
                ('ninnum', 'NIN #'),
                ('passport', 'Passport Number'),
                ('other', 'Other')
            ]
        cls.alternative_id_type.selection = selections[:]
        # for selection in selections:
        #     if selection not in cls.alternative_id_type.selection:
        #         cls.alternative_id_type.selection.append(selection)

    # @fields.depends('alternative_id_type')
    # def on_change_with_issuedby(self, *arg, **kwarg):
    #     print(('*'*20) + " on_change_with_issuedby " + ('*'*20) )
    #     print(repr(self.alternative_id_type))
    #     return ''

class PostOffice(ModelSQL, ModelView):
    'Country Post Office'
    __name__ = 'country.post_office'
    
    code = fields.Char('Code', required=True, size=10)
    name = fields.Char('Post Office', required=True, help="Post Offices")
    subdivision = fields.Many2One('country.subdivision', 'Parish/Province',
        help="Enter Parish, State or Province")
    inspectorate = fields.Char('Inspectorate', help="Postal Area that governs this office or agency")

    @classmethod
    def __setup__(cls):
        super(PostOffice, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
                'The Post Office code be unique !'),
        ]

    @classmethod
    def __register__(cls, module_name):
        '''handles the rewiring of the Jamaica parishes to merge Kingston and
        Saint Andrew (JM-01 and JM-02)'''
        super(PostOffice, cls).__register__(module_name)
        cursor = Transaction().cursor
        # update subdivision table to remove st. andrew and merge with Kgn
        cursor.execute('Select name from country_subdivision where code=%s',('JM-02',))
        standrew = cursor.fetchone()
        if standrew:
            sql = ['UPDATE country_subdivision set name=%s where code=%s',
                   'DELETE from country_subdivision where code=%s' ]
            parms = [('Kingston & Saint Andrew', 'JM-01'), ('JM-02',)]
            for query, query_param in zip(sql, parms):
                cursor.execute(query, query_param)
            cursor.commit()



class DistrictCommunity(ModelSQL, ModelView):
    'Country District Community'
    __name__ = 'country.district_community'
    
    name = fields.Char('District Community', required=True,
        help="District Communities")
    post_office = fields.Many2One('country.post_office', 'Post Office', 
        required=True)

    @classmethod
    def __setup__(cls):
        super(DistrictCommunity, cls).__setup__()
        cls._sql_constraints = [
            ('name_per_po_uniq', 'UNIQUE(name, post_office)',
                'The District Community must be unique for each post office!'),
        ]


class DomiciliaryUnit(ModelSQL, ModelView):
    'Domiciliary Unit'
    __name__ = 'gnuhealth.du'

    name = fields.Char('Code', readonly=True)
    address_street_num = fields.Char('Street Number', size=8)
    address_post_office = fields.Many2One(
        'country.post_office', 'Post Office (JM)', help="Closest Post Office, Jamaica only",
        domain=[('subdivision', '=', Eval('address_subdivision'))],
        depends=['address_subdivision'])
    address_subdivision = fields.Many2One(
        'country.subdivision', 'Parish/Province',
        domain=[('country', '=', Eval('address_country'))],
        depends=['address_country'], help="Select Parish, State or Province")
    address_district_community = fields.Many2One(
        'country.district_community', 'District (JM)',
        domain=[('post_office', '=', Eval('address_post_office'))],
        depends=['address_post_office'], help="Select District/Community, Jamaica only")
    desc = fields.Char('Additional Description')
    city_town = fields.Function(fields.Char('City/Town/P.O.'), 'get_city_town')

    @classmethod
    def default_country(cls):
        return JAMAICA()

    def get_city_town(self, name):
        '''returns the post office for jamaica or the city or municipality for
        other addresses'''

        if self.address_country == JAMAICA() and self.address_post_office:
            return self.address_post_office.name
        else:
            return self.address_city or self.address_municipality

    # @fields.depends('address_subdivision')
    # def on_change_with_name(self, *arg, **kwarg):
    #     ''' generates domunit code as follows :
    #     PARISHCODE-{RANDOM_HEX_DIGITSx8}.
    #     The parish code is taken directly from the parish when selected or 
    #     when a post office is selected. The RANDOM_HEX_DIGITSx8 is the
    #     first 8 chars from the SHA1 hash of [self.desc, self.post_office.code,
    #                 self.address_district_community.name,
    #                 self.address_street, self.address_street_num,
    #                 self.address_street_bis]) #, str(time.time())])
    #     separated by semi-colon (;)
    #     '''
    #     codelist = []
    #     if self.address_subdivision:
    #         codelist.append(self.address_subdivision.code)
    #     else :
    #         return ''

    #     hashlist = filter(None, [self.desc, 
    #                 self.address_post_office and self.address_post_office.code or '',
    #                 self.address_district_community and self.address_district_community.name or '',
    #                 self.address_street, self.address_street_num,
    #                 self.address_street_bis]) #, str(time.time())])

    #     codelist.append(hashlib.sha1(';'.join(hashlist)).hexdigest()[:8])

    #     return '-'.join(codelist)

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
                values['name'] = cls.generate_du_code(state_code,
                    *[values.get(r) for r in ('desc','address_post_office',
                                              'address_district_community',
                                              'address_street',
                                              'address_street_num',
                                              'address_street_bis')])
        return super(DomiciliaryUnit, cls).create(vlist)


class Newborn (ModelSQL, ModelView):
    'Newborn Information'
    __name__ = 'gnuhealth.newborn'
    
    bba = fields.Boolean('BBA', help='Check this box if born on arrival to health facility')
    cephalic_perimeter = fields.Integer('Head Circumference',
        help="Perimeter in centimeters (cm)")
    length = fields.Integer('Crown-Heel Length', help="Length in centimeters (cm)")


class Insurance(ModelSQL, ModelView):
    'Insurance'
    __name__ = 'gnuhealth.insurance' #database table, tryton translates this into gnuhealth_insurance
    _rec_name = 'number'

    # Insurance associated to an individual

    name = fields.Many2One('party.party', 'Owner')
    number = fields.Char('Policy#', required=True)

    def get_rec_name(self, name):
        return (self.company.name + ' : ' + self.number)

class HealthProfessional(ModelSQL, ModelView):
    'Health Professional'
    __name__ = 'gnuhealth.healthprofessional'

    def get_rec_name(self, name):
        if self.name:
            return self.name.name
