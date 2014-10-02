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
import re
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal, And, Or
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['PartyPatient', 'PatientData', 'AlternativePersonID', 'PostOffice',
    'DistrictCommunity', 'DomiciliaryUnit', 'Newborn', 'Insurance',
    'PartyAddress', 'HealthProfessional', 'Appointment']
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
    maiden_name = fields.Char('Maiden Name', 
                          states={'invisible':Or(Not(Equal(Eval('marital_status'), 'm')), Equal(Eval('sex'), 'm'))})

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
            'invisible': And(Not(Bool(Eval('unidentified'))),
                             Not(Bool(Eval('ref')))),
            'readonly': Bool(Eval('party_warning_ack'))
            })

    occupation = fields.Many2One('gnuhealth.occupation', 'Occupational Group')
    insurance = fields.One2Many('gnuhealth.insurance', 'name', 'Insurance',
        help="Insurance Plans associated to this party")
    medical_record_num = fields.Function(fields.Char('Medical Record Num.'),
        'get_alt_ids', searcher='search_alt_ids')
    alt_ids = fields.Function(fields.Char('Alternate IDs'), 'get_alt_ids',
        searcher='search_alt_ids')

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
            '== Indentity Verification ==\n\n'
            'Please enter an Alternative ID before declaring\n'
            'that the party\'s identity has been verified.\n',
            'future_dob_error':'== Error ==\n\nDate of birth cannot be in the future.',
            'unidentified_or_altid':'== Party Identification ==\n\n'
                        'Please check the unidentified box or add an alternative id'
        })

    @staticmethod
    def default_unidentified():
        return True

    @staticmethod
    def default_alternative_identification():
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
            party.check_dob()

    @classmethod
    def write(cls, parties, vals):
        regex = re.compile(u'NN-([A-Z]{3}\d{3}[A-Z]{3})')
        for party in parties:
            if vals.get('party_warning_ack') and regex.match(party.ref):
                # remove the NN from the UPI
                vals['ref'] = ''.join(regex.split(party.ref))
        return super(PartyPatient, cls).write(parties, vals)

    def check_party_warning(self):
        '''validates that a party being entered as verified has an alt-id
        if there is no alt-id, then the party should be labeled as unidentified
        '''
        if len(self.alternative_ids) == 0 and not self.unidentified:
            self.raise_user_error('unidentified_or_altid')

        if len(self.alternative_ids) == 0 and self.party_warning_ack:
            self.raise_user_error('unidentified_party_warning')

    def check_dob(self):
        if self.dob and self.dob > date.today():
            self.raise_user_error('future_dob_error')

    def get_alt_ids(self, field_name):
        if (field_name == 'medical_record_num'):
            for altid in self.alternative_ids:
                if altid.alternative_id_type == 'medical_record':
                    return altid.code
            return '--'
        else:
            altids = []
            for altid in self.alternative_ids:
                if altid.alternative_id_type != 'medical_record':
                    altids.append('-'.join([altid.alternative_id_type,altid.code]))
            return ', '.join(altids)


    @classmethod
    def search_alt_ids(cls, field_name, clause):
        if field_name == 'medical_record_num':
            return ['AND',(('alternative_ids.alternative_id_type','=','medical_record'),
                    ('alternative_ids.code',)+tuple(clause[1:]))]
        else:
            return ['AND',(
            ('alternative_ids.alternative_id_type','!=','medical_record'),
            ('alternative_ids.code', clause[1], clause[2]))]

    def get_person_field(self, field_name):
        return getattr(self.name, field_name)

    @classmethod
    def search_person_field(cls, field_name, clause):
        return [('name.{}'.format(field_name), clause[1], clause[2])]



class PatientData(ModelSQL, ModelView):
    '''Patient related information, redefined to fix name display/generation'''
    __name__ = 'gnuhealth.patient'

    name = fields.Many2One(
        'party.party', 'Patient', required=True,
        domain=[
            ('is_patient', '=', True),
            ('is_person', '=', True),
            ],
        # states={'readonly': Bool(Eval('name'))},
        help="Person that is this patient")

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
    dob = fields.Function(fields.Date('DOB'), 'get_person_field',
                                searcher='search_person_field')
    firstname = fields.Function(fields.Char('First name'), 'get_person_field',
                                searcher='search_person_field')
    middlename = fields.Function(fields.Char('Middle name'), 'get_person_field',
                                searcher='search_person_field')
    mother_maiden_name = fields.Function(fields.Char('Mother\'s maiden name'),
                                'get_person_field', searcher='search_person_field')
    father_name = fields.Function(fields.Char('Father\'s name'), 'get_person_field',
                                searcher='search_person_field')
    medical_record_num = fields.Function(fields.Char('Medical Record Number'),
        'get_person_field', searcher='search_alt_ids')
    alt_ids = fields.Function(fields.Char('Alternate IDs'), 'get_person_field',
        searcher='search_alt_ids')
    du = fields.Function(fields.Char('Domiciliary Unit'),
                            'get_person_field', searcher='search_person_field')

    def get_rec_name(self, name):
        return self.name.name

    @classmethod
    def __setup__(cls):
        super(PatientData, cls).__setup__()
        cls.puid.string = 'UPI'

    def get_person_field(self, field_name):
        return getattr(self.name, field_name)

    @classmethod
    def search_person_field(cls, field_name, clause):
        return [('name.{}'.format(field_name), clause[1], clause[2])]

    @classmethod
    def search_alt_ids(cls, field_name, clause):
        if field_name == 'medical_record_num':
            return ['AND',(('name.alternative_ids.alternative_id_type','=','medical_record'),
                    ('name.alternative_ids.code',)+tuple(clause[1:]))]
        else:
            return ['AND',(
            ('name.alternative_ids.alternative_id_type','!=','medical_record'),
            ('name.alternative_ids.code', clause[1], clause[2]))]

    # Get the patient age in the following format : 'YEARS MONTHS DAYS'
    # It will calculate the age of the patient while the patient is alive.
    # When the patient dies, it will show the age at time of death.

    def patient_age(self, name):

        def compute_age_from_dates(patient_dob, patient_deceased,
                                   patient_dod, patient_sex):

            now = datetime.now()

            if (patient_dob):
                dob = datetime.strptime(str(patient_dob), '%Y-%m-%d')

                if patient_deceased:
                    dod = datetime.strptime(
                        str(patient_dod), '%Y-%m-%d %H:%M:%S')
                    delta = relativedelta(dod, dob)
                    deceased = '(deceased)'
                else:
                    delta = relativedelta(now, dob)
                    deceased = ''
                ymd = []
                if delta.years >= 1:
                    ymd.append(str(delta.years) + 'y')
                if (delta.months >0 or delta.years > 0) and delta.years < 10:
                    ymd.append(str(delta.months) + 'm')
                if delta.years <= 2: 
                    ymd.append(str(delta.days) + 'd')
                ymd.append(deceased)

                years_months_days = ' '.join(ymd)
            else:
                years_months_days = '--'

            # Return the age in format y m d when the caller is the field name
            if name == 'age':
                return years_months_days

            # Return if the patient is in the period of childbearing age >10 is
            # the caller is childbearing_potential

            if (name == 'childbearing_age' and patient_dob):
                if (delta.years >= 11
                   and delta.years <= 55 and patient_sex == 'f'):
                    return True
                else:
                    return False

        return compute_age_from_dates(self.dob, self.deceased,
                                      self.dod, self.sex)


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
        cls._error_messages.update({
            'invalid_trn':'Invalid format for TRN',
            'invalid_medical_record': 'Invalid format for medical record number',
            'invalid_format':'Invalid format'
        })
        cls.format_test = {
            'trn':re.compile('1\d{8}'),
            'medical_record': re.compile('\d{6}[a-z]?', re.I),
            'pathID':re.compile('\d{8}'),
            'gojhcard':re.compile('\d{10}'),
            'nunnum':re.compile('\d{9}')
        }
        # for selection in selections:
        #     if selection not in cls.alternative_id_type.selection:
        #         cls.alternative_id_type.selection.append(selection)

    # @fields.depends('alternative_id_type')
    # def on_change_with_issuedby(self, *arg, **kwarg):
    #     print(('*'*20) + " on_change_with_issuedby " + ('*'*20) )
    #     print(repr(self.alternative_id_type))
    #     return ''

    @classmethod
    def validate(cls, records):
        super(AlternativePersonID, cls).validate(records)
        for alternative_id in records:
            alternative_id.check_format()

    def check_format(self):
        format_tester = self.format_test.get(self.alternative_id_type, False)
        if format_tester:
            if format_tester.match(self.code):
                pass
            else:
                error_msg = 'invalid_{}'.format(self.alternative_id_type)
                if not self._error_messages.has_key(error_msg):
                    error_msg = 'invalid_format'
                self.raise_user_error(error_msg)


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


ADDRESS_STATES = { 'readonly': ~Eval('active')}
ADDRESS_DEPENDS = ['active']

class PartyAddress(ModelSQL, ModelView):
    'Party Address, defines parties that are related to patients'
    __name__ = 'party.address'

    relationship = fields.Selection([
        ('', ''),
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
        ('other', 'Other')
        ],'Relationship', help="Relationship of contact to patient", sort=False)


    streetbis = fields.Char('Apartment/Suite #', states=ADDRESS_STATES,
        depends=ADDRESS_DEPENDS)
    subdivision = fields.Many2One("country.subdivision",
            'Parish/Province', domain=[('country', '=', Eval('country'))],
            states=ADDRESS_STATES, depends=['active', 'country'])
    address_street_num = fields.Char('Street Number', size=8,
        states=ADDRESS_STATES)
    post_office = fields.Many2One(
        'country.post_office', 'Post Office (JM)', help="Closest Post Office, Jamaica only",
        domain=[('subdivision', '=', Eval('subdivision'))],
        depends=['subdivision'], states=ADDRESS_STATES)
    district_community = fields.Many2One(
        'country.district_community', 'District (JM)', states=ADDRESS_STATES,
        domain=[('post_office', '=', Eval('post_office'))],
        depends=['post_office'], help="Select District/Community, Jamaica only")
    desc = fields.Char('Additional Description', states=ADDRESS_STATES,
        help="Landmark or additional directions")
 

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
    desc = fields.Char('Additional Description',
        help="Landmark or additional directions")
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


class Appointment(ModelSQL, ModelView):
    'Patient Appointments'
    __name__ = 'gnuhealth.appointment'

    state = fields.Selection([
        (None, ''),
        ('free', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('user_cancelled', 'Cancelled by patient'),
        ('center_cancelled', 'Cancelled by Health Center'),
        ('no_show', 'No show')
        ], 'State', sort=False)

    @staticmethod
    def default_state():
        return 'free'

    @classmethod
    def __register__(cls, module_name):
        '''hack to rename the window title from free to scheduled'''
        super(Appointment, cls).__register__(module_name)
        cursor = Transaction().cursor
        # update ir_action_act_window_domain table to change name from free
        cursor.execute('Select count(*) from ir_action_act_window_domain where name=%s',('Free',))
        freetab = cursor.fetchone()
        if freetab and freetab[0] == 1:
            sql = 'UPDATE ir_action_act_window_domain set name=%s where name=%s'
            parms = ('Scheduled', 'Free')
            cursor.execute(sql, parms)
            cursor.commit()