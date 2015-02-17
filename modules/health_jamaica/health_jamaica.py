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
import six
import uuid
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal, And, Or
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.config import CONFIG

from .tryton_utils import (negate_clause, replace_clause_column,
                           make_selection_display, get_timezone,
                           is_not_synchro)

__all__ = ['PartyPatient', 'PatientData', 'AlternativePersonID', 'PostOffice',
    'DistrictCommunity', 'DomiciliaryUnit', 'Newborn', 'HealthInstitution',
    'Insurance', 'PartyAddress', 'HealthProfessional', 'Appointment', 
    'DiagnosticHypothesis', 'PathologyGroup', 'PatientEvaluation',
    'SignsAndSymptoms', 'OccupationalGroup', 'HealthProfessionalSpecialties',
    'HealthInstitutionSpecialties', 'ProcedureCode']
__metaclass__ = PoolMeta

_STATES = {
    'invisible': Not(Bool(Eval('is_person'))),
}
_DEPENDS = ['is_person']

JAMAICA_ID=89
JAMAICA = lambda : Pool().get('country.country')(JAMAICA_ID)
ThisInstitution = lambda : Pool().get('gnuhealth.institution').get_institution()
SEX_OPTIONS = [('m', 'Male'), ('f', 'Female'), ('u', 'Unknown')]
MARITAL_STATUSES = [
        ('s', 'Single'),
        ('m', 'Married'),
        ('c', 'Living with partner'),
        ('v', 'Visiting'),
        ('w', 'Widowed'),
        ('d', 'Divorced'),
        ('x', 'Separated'),
        ('n', 'Not Applicable'),
        ('u', 'Unknown')]
ALTERNATIVE_ID_TYPES = [
        ('trn','TRN'),
        ('medical_record', 'Medical Record'),
        ('pathID','PATH ID'),
        ('gojhcard','GOJ Health Card'),
        ('votersid','GOJ Voter\'s ID'),
        ('birthreg', 'Birth Registration ID'),
        ('ninnum', 'NIN #'),
        ('passport', 'Passport'),
        ('jm_license', 'Drivers License (JM)'),
        ('nonjm_license', 'Drivers License (non-JM)'),
        ('other', 'Other')]

SYNC_ID=int(CONFIG.get('synchronisation_id','1'))
# Default sync ID to 1 so it doesn't think it's the master

NNre = re.compile('(%?)NN-(.*)', re.I)


class OccupationalGroup(ModelSQL, ModelView):
    '''Occupational Group'''
    __name__ = 'gnuhealth.occupation'

    @classmethod
    def __register__(cls, module_name):
        super(OccupationalGroup, cls).__register__(module_name)
        # remove the occupations from the table that don't have 4 char codes
        cursor = Transaction().cursor
        cursor.execute('select count(*) from gnuhealth_occupation where char_length(code)=4;')
        possibly_valid, = cursor.fetchone()
        if possibly_valid == 0:
            cursor.execute('delete from gnuhealth_occupation where char_length(code)<4;')
            cursor.execute('alter sequence gnuhealth_occupation_id_seq restart with 1;')
        else:
            print('Mixed occupation list, cannot auto-resolve. Fix by hand')


class PartyPatient (ModelSQL, ModelView):
    'Party'
    __name__ = 'party.party'
    
    ref = fields.Char(
        'UPI',
        help='Universal Person Indentifier',
        states=_STATES, depends=_DEPENDS, readonly=True)
    upi = fields.Function(fields.Char('UPI', help='Universal Person Identifier'),
                          'get_upi_display', searcher='search_upi')
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

    marital_status = fields.Selection([(None, '')]+MARITAL_STATUSES,
                                      'Marital Status', sort=False)
    marital_status_display = fields.Function(fields.Char('Marital Status'),
                                             'get_marital_status_display')

    # gender vs sex: According to the AMA Manual of Style :
    # Gender refers to the psychological/societal aspects of being male or female,
    # sex refers specifically to the physical aspects. Do not interchange
    sex = fields.Selection([(None,'')] + SEX_OPTIONS,
                           'Sex', states={'required':Bool(Eval('is_person'))})
    sex_display = fields.Function(fields.Char('Sex'), 'get_sex_display')
    party_warning_ack = fields.Boolean('Party verified', 
        states={
            'invisible': And(Not(Bool(Eval('unidentified'))),
                             Not(Bool(Eval('ref')))),
            'readonly': Bool(Eval('party_warning_ack'))
            })

    occupation = fields.Many2One('gnuhealth.occupation', 'Occupational Group')
    insurance = fields.One2Many('gnuhealth.insurance', 'name', 'Insurance',
        help="Insurance Plans associated to this party")
    du = fields.Many2One('gnuhealth.du', 'Address')
    internal_user = fields.Many2One(
        'res.user', 'Internal User',
        help='In order for this health professional to use the system, an'
        ' internal user account must be assigned. This health professional'
        ' will have a user account on this instance only.',
        states={
            'invisible': Not(Bool(Eval('is_healthprof'))),
            'required': False,
            })
    medical_record_num = fields.Function(fields.Char('Medical Record Num.'),
        'get_alt_ids', searcher='search_alt_ids')
    alt_ids = fields.Function(fields.Char('Alternate IDs'), 'get_alt_ids',
        searcher='search_alt_ids')

    def get_rec_name(self, name):
        # simplified since we generate the person name and all others are okay
        return self.name

    def get_upi_display(self, name):
        if self.party_warning_ack or not self.is_patient:
            return self.ref
        else:
            return u'NN-{}'.format(self.ref)

    @classmethod
    def search_upi(cls, field_name, clause):
        fld, operator, operand = clause
        if (isinstance(operand, six.string_types) and
            NNre.match(operand)):
            # searching for NN- records, so auto-append verified=False
            operand = u''.join(NNre.split(operand))
            if operand == u'%%': operand = '%'
            return ['AND', ('ref',operator, operand),
                           ('party_warning_ack','=', False)]
        else:
            return [replace_clause_column(clause, 'ref')]

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
            namelist = [''.join((self.lastname,',')), self.firstname]
        if self.middlename:
            namelist.append(self.middlename)
        return ' '.join(namelist)

    @classmethod
    def generate_upc(cls):
        # Add a default random string in the ref field.
        # The STRSIZE constant provides the length of the HIN
        # The format of the UPC is XXXNNNXXX
        STRSIZE = 9
        letters = ('ABCDEFGHJKLMNPRTUWXY')
        # letters removed = IOQSVZ because they look too similar to numbers
        # or to other letters. 
        hin = ''
        for x in range(STRSIZE): 
            if ( x < 3 or x > 5 ):
                hin = hin + random.choice(letters)
            else:
                hin = hin + random.choice(string.digits)
        return hin

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('party.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not 'ref' in values or not values['ref'] :
                values['ref'] = cls.generate_upc()
                if 'is_person' in values and not values['is_person']:
                    values['ref'] = 'NP-' + values['ref']

            if not values.get('code'):
                config = Configuration(1)
                # Use the company name . Initially, use the name
                # since the company hasn't been created yet.
                institution_id = ThisInstitution()
                if institution_id:
                    institution = Pool().get('gnuhealth.institution')(institution_id)
                    suffix = institution.code
                else:                    
                    suffix = Transaction().context.get('company.rec_name') \
                        or values['name']
                values['code'] = '-'.join([str(x) for x in 
                                          (uuid.uuid4(), suffix)])

            values.setdefault('addresses', None)
        return super(PartyPatient, cls).create(vlist)

    @classmethod
    def validate(cls, parties):
        super(PartyPatient, cls).validate(parties)
        # since these validations only matter for regular users of the 
        # system, we will not perform the checks if the transaction's user
        # id is 0. The sync-engine sets the user to 0 on both ends of the 
        # connection. All regular users get their user ID in this space

        if is_not_synchro():
            for party in parties:
                party.check_party_warning()
                party.check_dob()

    # @classmethod
    # def write(cls, *args):
    #     regex = re.compile(u'NN-([A-Z]{3}\d{3}[A-Z]{3})')
    #     actions = iter(args)
    #     for parties, vals in zip(actions, actions):
    #         if vals.get('party_warning_ack'):
    #             for party in parties:
    #                 if regex.match(party.ref):
    #                     # remove the NN from the UPI
    #                     vals['ref'] = ''.join(regex.split(party.ref))
    #     return super(PartyPatient, cls).write(*args)

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

        here = ThisInstitution()
        id_type_map = dict(ALTERNATIVE_ID_TYPES)
        if (field_name == 'medical_record_num'):
            for altid in self.alternative_ids:
                if (altid.alternative_id_type == 'medical_record' and
                    (altid.issuing_institution and 
                     altid.issuing_institution.id==here)):
                    return altid.code
            return '--'
        else:
            altids = []
            for altid in self.alternative_ids:
                if (altid.alternative_id_type == 'medical_record' and
                    altid.issuing_institution and
                    altid.issuing_institution.id == here):
                    continue
                else:
                    a_type = id_type_map.get(altid.alternative_id_type, 
                                             altid.alternative_id_type)
                    altids.append('{} {}'.format(a_type, altid.code))
            return '; '.join(altids)


    @classmethod
    def search_alt_ids(cls, field_name, clause):
        if field_name == 'medical_record_num':
            return ['AND',('alternative_ids.alternative_id_type','=','medical_record'),
                    ('alternative_ids.code',)+tuple(clause[1:])]
        else:
            return ['AND',
            ('alternative_ids.alternative_id_type','!=','medical_record'),
            ('alternative_ids.code', clause[1], clause[2])]

    def get_person_field(self, field_name):
        return getattr(self.name, field_name)

    @classmethod
    def search_person_field(cls, field_name, clause):
        return [('name.{}'.format(field_name), clause[1], clause[2])]

    def get_sex_display(self, field_name):
        sex_dict = dict(SEX_OPTIONS)
        return sex_dict.get(self.sex, '')

    def get_marital_status_display(s,n):
        return make_selection_display()(s,'marital_status')


BloodDict = dict([('{}{}'.format(t,r),(t,r)) for t in ['A','B','AB','O']
                    for r in ['+','-']])


class PatientData(ModelSQL, ModelView):
    '''Patient related information, redefined to fix name display/generation'''
    __name__ = 'gnuhealth.patient'

    name = fields.Many2One(
        'party.party', 'Patient', required=True,
        domain=[
            ('is_patient', '=', True),
            ('is_person', '=', True),
            ],
        # states = {'readonly': Eval('id', 0) > 0},
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
    sex_display = fields.Function(fields.Char('Sex'), 'get_person_field')
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
    du = fields.Function(fields.Char('Address'),
                            'get_person_field', searcher='search_person_field')
    unidentified = fields.Function(fields.Boolean('Unidentified'),
        'get_unidentified', searcher='search_unidentified')

    blood_rh = fields.Function(
                fields.Selection([(None, '')]+[(x,x) for x in BloodDict.keys()],
                                 'Blood type'),
                'get_blood_rh', 'set_blood_rh', searcher='search_blood_rh')

    def get_rec_name(self, name):
        return self.name.name

    @classmethod
    def __setup__(cls):
        super(PatientData, cls).__setup__()
        cls.puid.string = 'UPI'

    def get_person_field(self, field_name):
        return getattr(self.name, field_name)

    def get_unidentified(self, field_name):
        if self.name.unidentified and not self.name.party_warning_ack:
            return True
        else:
            return False

    @classmethod
    def search_person_field(cls, field_name, clause):
        return [('name.{}'.format(field_name), clause[1], clause[2])]

    @classmethod
    def search_alt_ids(cls, field_name, clause):
        if field_name == 'medical_record_num':
            return ['AND',('name.alternative_ids.alternative_id_type','=','medical_record'),
                    ('name.alternative_ids.code',)+tuple(clause[1:])]
        else:
            return ['AND',
            ('name.alternative_ids.alternative_id_type','!=','medical_record'),
            ('name.alternative_ids.code', clause[1], clause[2])]

    @classmethod
    def search_unidentified(cls, field_name, clause):
        cond = ['AND', replace_clause_column(clause, 'name.unidentified'),
                negate_clause(replace_clause_column(clause,
                                                    'name.party_warning_ack'))
               ]
        # print(repr(cond))
        return cond

    def get_patient_puid(self, name):
        return self.name.get_upi_display('upi')

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

                # Return the raw age in the integers array [Y,M,D]
                # When name is 'raw_age'
                if name == 'raw_age':
                    return [delta.years,delta.months,delta.days]

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
    
    @classmethod
    def search_blood_rh(cls, field_name, clause):
        res = []
        real_val = BloodDict.get(clause[2])
        if real_val:
            res = ['AND', ('blood_type',clause[1], real_val[0]),
                   ('rh',clause[1],real_val[1])]

        return res

    @classmethod
    def set_blood_rh(cls, ids, name, value):
        real_val = BloodDict.get(value, '')
        if real_val:
            self.blood_type,self.rh = real_val
        else:
            self.blood_type,self.rh = None,None


    def get_blood_rh(self, field_name):
        if self.blood_type and self.rh:
            return '{}{}'.format(self.blood_type,self.rh)

class AlternativePersonID (ModelSQL, ModelView):
    'Alternative person ID'
    __name__ ='gnuhealth.person_alternative_identification' 
   
    issuing_institution = fields.Many2One('gnuhealth.institution', 'Issued By',
        help='Institution that assigned the medical record number',
        states={'required':Eval('alternative_id_type') == 'medical_record'},
        depends=['alternative_id_type'])
    expiry_date = fields.Date('Expiry Date')
    issue_date = fields.Date('Date Issued')
    type_display = fields.Function(fields.Char('ID Type'), 'get_type_display')

    @classmethod
    def __setup__(cls):
        super(AlternativePersonID, cls).__setup__()
        
        cls.alternative_id_type.selection = ALTERNATIVE_ID_TYPES[:]
        cls._error_messages.update({
            'invalid_trn':'Invalid format for TRN',
            'invalid_jm_license':'Invalid format for Jamaican Drivers License.\n Numbers only please.',
            'invalid_medical_record': 'Invalid format for medical record number',
            'invalid_format':'Invalid format for %s',
            'mismatched_issue_expiry':'%s issue date cannot be after the expiry date',
            'expiry_date_required':'An expiry date is required for %s'
        })
        cls.format_test = {
            'trn':re.compile('^1\d{8}$'),
            'medical_record': re.compile('\d{6}[a-z]?', re.I),
            'pathID':re.compile('^\d{8}$'),
            'gojhcard':re.compile('^\d{10}$'),
            'nunnum':re.compile('^\d{9}$')
        }
        cls.format_test['jm_license'] = cls.format_test['trn']
        cls.expiry_required = ('passport', 'jm_license', 'nonjm_license')
        # for selection in selections:
        #     if selection not in cls.alternative_id_type.selection:
        #         cls.alternative_id_type.selection.append(selection)

        # cls.get_altid_type = lambda x : dict(selections).get(x,'')

    def get_type_display(self, fn):
        return make_selection_display()(self, 'alternative_id_type')

    @fields.depends('alternative_id_type')
    def on_change_with_issuing_institution(self, *a, **k):
        '''set this institution as the issuing instution whenever
            medical record selected as the ID type'''

        if self.alternative_id_type == 'medical_record':
            institution = Pool().get('gnuhealth.institution').get_institution()
            if institution:
                return institution

        return None

    @classmethod
    def validate(cls, records):
        super(AlternativePersonID, cls).validate(records)
        for alternative_id in records:
            alternative_id.check_format()
            if (alternative_id.expiry_date and alternative_id.issue_date and
                alternative_id.issue_date > alternative_id.expiry_date):
                    alternative_id.raise_user_error(
                                        'mismatched_issue_expiry',
                                        (alternative_id.type_display,))
            if (not alternative_id.expiry_date and 
                alternative_id.alternative_id_type in cls.expiry_required):
                    alternative_id.raise_user_error(
                                        'expiry_date_required',
                                        (alternative_id.type_display,))


    def check_format(self):
        format_tester = self.format_test.get(self.alternative_id_type, False)
        if format_tester:
            if format_tester.match(self.code):
                pass
            else:
                error_msg = 'invalid_{}'.format(self.alternative_id_type)
                if not self._error_messages.has_key(error_msg):
                    error_msg = 'invalid_format'
                self.raise_user_error(error_msg, (self.type_display,))


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
                'The Post Office code be unique.'),
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
    
    code = fields.Char('Code', required=True, size=10)
    name = fields.Char('District Community', required=True,
        help="District Communities")
    post_office = fields.Many2One('country.post_office', 'Post Office', 
        required=True)

    @classmethod
    def __setup__(cls):
        super(DistrictCommunity, cls).__setup__()
        cls._sql_constraints = [
            ('name_per_po_uniq', 'UNIQUE(name, post_office)',
                'The District Community must be unique for each post office.'),
            ('code_uniq', 'UNIQUE(code)',
                'The Community code be unique.'),
        ]


ADDRESS_STATES = { 'readonly': ~Eval('active')}
ADDRESS_DEPENDS = ['active']

class PartyAddress(ModelSQL, ModelView):
    'Party Address'
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
    full_address = fields.Function(fields.Text('Full Address'),
            'get_full_address')
    simple_address = fields.Function(fields.Text('Simple Address'),
            'get_full_address')
    relationship_display = fields.Function(fields.Char('Relationship'),
                                           'get_relationship_display')

    @classmethod
    def default_country(cls):
        return JAMAICA_ID

    def get_full_address(self, name):
        if self.country and self.country.id == JAMAICA_ID:
            addr,line = [],[]
            if self.address_street_num: line.append(self.address_street_num)
            if self.street: line.append(','.join([self.street,'']))
            if self.streetbis: line.extend([' Apt#', self.streetbis])
            if line:
                addr.append(u' '.join(line[:]))
                line =[]
            if self.district_community and self.district_community.id:
                line.append(','.join([self.district_community.name,'']))

            if self.post_office:
                line.append(self.post_office.name)

            if line:
                addr.append(u' '.join(line[:]))
                line=[]

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

class DomiciliaryUnit(ModelSQL, ModelView):
    'Domiciliary Unit'
    __name__ = 'gnuhealth.du'

    name = fields.Char('Code', required=False, readonly=True)
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
    # address_district = fields.Char(
    #     'District', help="Neighborhood, Village, Barrio....",
    #     states={'invisible':Eval('address_country')==89})
    # address_municipality = fields.Char(
    #     'Municipality', help="Municipality, Township, county ..",
    #     states={'invisible':Eval('address_country')==89})
    # address_zip = fields.Char('Zip Code',
    #     states={'invisible':Eval('address_country')==89})
    city_town = fields.Function(fields.Char('City/Town/P.O.'), 'get_city_town')

    full_address = fields.Function(fields.Text('Full Address'),
            'get_full_address')
    simple_address = fields.Function(fields.Text('Address'),
                                     'get_full_address')

    @classmethod
    def default_address_country(cls):
        return JAMAICA_ID

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
            if self.address_country.id == JAMAICA_ID:
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


class Newborn (ModelSQL, ModelView):
    'Newborn Information'
    __name__ = 'gnuhealth.newborn'
    
    bba = fields.Boolean('BBA', help='Check this box if born on arrival to health facility')
    cephalic_perimeter = fields.Integer('Head Circumference',
        help="Perimeter in centimeters (cm)")
    length = fields.Integer('Crown-Heel Length', help="Length in centimeters (cm)")


class HealthInstitution(ModelSQL, ModelView):
    'Health Institution'
    __name__ = 'gnuhealth.institution'

    main_specialty = fields.Function(
                        fields.Many2One('gnuhealth.institution.specialties',
                            'Specialty',
                            domain=[('name', '=', 
                                     Eval('active_id'))], 
                            depends=['specialties'], 
        help="Choose the speciality in the case of Specialized Hospitals" \
            " or where this center excels",
        # Allow to select the institution specialty only if the record already
        # exists
        states={'required': And(Eval('institution_type') == 'specialized',
            Eval('id', 0) > 0),
            'readonly': Eval('id', 0) < 0}),
                        'get_main_specialty',
                        'set_main_specialty',
                        'search_main_specialty'
    )

    def get_main_specialty(self, name):
        mss = [x for x in self.specialties if x.is_main_specialty]
        if mss:
            return mss[0].id
        return None

    @classmethod
    def search_main_specialty(cls, name, clause):
        return ['AND',
            ('specialties.is_main_specialty','=',True),
            replace_clause_column(clause, 'specialties.specialty.id')
        ]

    @classmethod
    def set_main_specialty(cls, instances, field_name, value):
        for i in instances:
            turnoff,turnon = [],[]
            for spec in i.specialties:
                if spec.id == value:
                    turnon.append(spec)
                elif spec.is_main_specialty:
                    turnoff.append(spec)
        HIS = Pool().get('gnuhealth.institution.specialties')
        if turnoff:
            HIS.write(turnoff,{'is_main_specialty':None})
        if turnon:
            HIS.write(turnon, {'is_main_specialty':True})


class HealthInstitutionSpecialties(ModelSQL, ModelView):
    'Health Institution Specialties'
    __name__ = 'gnuhealth.institution.specialties'

    is_main_specialty = fields.Boolean('Main Specialty',
                                       help="Check if this is the main specialty"\
                                       " e.g. in the case of specialized hospital"\
                                       " or an area in which this institution excels.")
    @staticmethod
    def default_is_main_specialty():
        return False


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

    main_specialty = fields.Function(fields.Many2One('gnuhealth.hp_specialty',
                                                     'Main Specialty',
                                                     domain=[('name', '=', 
                                                              Eval('active_id'))]),
                                     'get_main_specialty',
                                     'set_main_specialty',
                                     'search_main_specialty')

    def get_rec_name(self, name):
        return self.name.name

    def get_main_specialty(self, name):
        mss = [x for x in self.specialties if x.is_main_specialty]
        if mss:
            return mss[0].id
        return None

    @classmethod
    def search_main_specialty(cls, name, clause):
        return ['AND',
            ('specialties.is_main_specialty','=',True),
            replace_clause_column(clause, 'specialties.specialty.id')
        ]

    @classmethod
    def set_main_specialty(cls, instances, field_name, value):
        for i in instances:
            turnoff,turnon = [],[]
            for spec in i.specialties:
                if spec.id == value:
                    turnon.append(spec)
                elif spec.is_main_specialty:
                    turnoff.append(spec)
        HPS = Pool().get('gnuhealth.hp_specialty')
        if turnoff:
            HPS.write(turnoff,{'is_main_specialty':None})
        if turnon:
            HPS.write(turnon, {'is_main_specialty':True})


class HealthProfessionalSpecialties(ModelSQL, ModelView):
    'Health Professional Specialties'
    __name__ = 'gnuhealth.hp_specialty'
    is_main_specialty = fields.Boolean('Main Specialty',
                                       help="Check if this is the main specialty"\
                                       " i.e. in the case of specialty doctor"\
                                       " or an area in which this professional excels.")

    @staticmethod
    def default_is_main_specialty():
        return False


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

    speciality = fields.Many2One(
        'gnuhealth.specialty', 'Specialty',
        help='Medical Specialty / Sector', states={'required':True})

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

    @classmethod
    def validate(cls, appointments):
        super(Appointment, cls).validate(appointments)
        for appt in appointments:
            if appt.patient:
                comp_startdate = datetime(*(appt.appointment_date.timetuple()[:3]+(0,0,0)),
                                          tzinfo=get_timezone())
                comp_enddate = datetime(*(appt.appointment_date.timetuple()[:3]+(23,59,59)),
                                          tzinfo=get_timezone())
                search_terms = ['AND',
                            ('patient','=',appt.patient),
                            ('appointment_date','>=',comp_startdate),
                            ('appointment_date','<=',comp_enddate)]
                if appt.id:
                    search_terms.append(('id','!=',appt.id))

                others = cls.search(search_terms)
            
            if others and is_not_synchro(): # pop up the warning but not during sync
                # setup warning params
                other_specialty = others[0].speciality.name
                warning_code = 'healthjm.duplicate_appointment_warning.w_{}_{}'.format(
                                appt.patient.id, appt.appointment_date.strftime('%s'))
                warning_msg = ['Possible Duplicate Appointment\n\n',
                                appt.patient.name.firstname,' ',
                                appt.patient.name.lastname]
                use_an = False
                if other_specialty == appt.speciality.name:
                    warning_msg.append(' already has')
                else:
                    warning_msg.append(' has')

                if re.match('^[aeiou].+', other_specialty, re.I):
                    warning_msg.append(' an ')
                else:
                    warning_msg.append(' a ')
                warning_msg.extend([other_specialty, ' appointment for ',
                                   appt.appointment_date.strftime('%b %d'),
                                  '\nAre you sure you need this ',
                                  appt.speciality.name, ' one?'])

                cls.raise_user_warning(warning_code, u''.join(warning_msg))


class ProcedureCode(ModelSQL, ModelView):
    'Medcal Procedures'
    __name__ = 'gnuhealth.procedure'
    @classmethod
    def __setup__(cls):
        super(ProcedureCode, cls).__setup__()
        if not isinstance(cls._sql_constraints, (list,)):
            cls._sql_constraints = []
        cls._sql_constraints.append(('name_uniq', 'UNIQUE(name)',
                                     'Medical procedure code must be unique'))


class PathologyGroup(ModelSQL, ModelView):
    'Pathology Groups'
    __name__ = 'gnuhealth.pathology.group'
    members = fields.One2Many ('gnuhealth.disease_group.members',
        'disease_group','Members', readonly=True)
    track_first = fields.Boolean('Track first diagnosis',
                                 help='Ask for status of first-diagnosis of diseases in this category upon creation of a diagnisis or diagnostic hypothesis',
                                )

    @staticmethod
    def default_track_first():
        return False


class DiagnosticHypothesis(ModelSQL, ModelView):
    'Diagnostic Hypotheses'
    __name__ = 'gnuhealth.diagnostic_hypothesis'

    # show_first_diagnosis = fields.Function(fields.Boolean('show first diag'),
    #                                        'get_sfd')
    first_diagnosis = fields.Boolean('First diagnosis', 
                         help='First time being diagnosed with this ailment',
                         states={'invisible':Bool(Eval('pathology.groups.disease_group.track_first'))},
                         depends=['pathology'])

    @staticmethod
    def default_first_diagnosis():
        return False

    @fields.depends('pathology')
    def on_change_pathology(self):
        val = False
        if self.pathology and self.pathology.groups:
            for g in self.pathology.groups:
                val |= g.disease_group.track_first
        self._show_first_diagnosis = val
        # ToDo: check if this is the first diagnosis for this disease
        return {'first_diagnosis':val}

    @classmethod
    def __setup__(cls):
        super(DiagnosticHypothesis, cls).__setup__()
        cls._show_first_diagnosis = False

    # def get_sfd(self, name):
    #     if hasattr(self,'_show_first_diagnosis'):
    #         pass
    #     else:
    #         if self.first_diagnosis:
    #             val = True
    #         else:
    #             val = False
    #             if self.pathology and self.pathology.groups:
    #                 for g in self.pathology.groups:
    #                     val |= g.disease_group.track_first                
    #         self._show_first_diagnosis = val
    #     return self._show_first_diagnosis


class PatientEvaluation(ModelSQL, ModelView):
    'Patient Evaluation'
    __name__ = 'gnuhealth.patient.evaluation'

    diagnostic_hypothesis = fields.One2Many(
        'gnuhealth.diagnostic_hypothesis',
        'evaluation', 'Hypotheses / DDx', help='Other Diagnostic Hypotheses /'
        ' Differential Diagnosis (DDx)', states={'required':False})
    first_visit_this_year = fields.Boolean('First visit this year',
                                           help='First visit this year')

    visit_type_display = fields.Function(fields.Char('Visit Type'),
                                         'get_selection_display')
    upi = fields.Function(fields.Char('UPI'), getter='get_person_patient_field')
    sex_display = fields.Function(fields.Char('Sex'), 'get_person_patient_field')
    age = fields.Function(fields.Char('Age'), 'get_person_patient_field')

    def get_selection_display(self, fn):
        return make_selection_display()(self,'visit_type')

    def get_person_patient_field(self, name):
        if name in ['upi', 'sex_display']:
            return getattr(self.patient.name, name)
        if name in ['age']:
            return getattr(self.patient, name)
        return ''

    def get_patient_age(self, name):
        if self.patient:
            return self.patient.patient_age(name)

    @fields.depends('patient', 'evaluation_start', 'institution')
    def on_change_with_first_visit_this_year(self, *arg, **kwarg):
        if self.institution and self.patient: # ToDo: Make sure to test for THIS YEAR
            M = Pool().get('gnuhealth.patient.evaluation')
            search_parms = [('evaluation_start','<',self.evaluation_start),
                            ('patient','=',self.patient.id),
                            ('institution', '=', self.institution.id)]

            others = M.search(search_parms)
            if others:
                return False

        return True

    @fields.depends('patient')
    def on_change_patient(self, *arg, **kwarg):
        return {'upi':self.patient.puid,
                'sex_display':self.patient.name.sex_display,
                'age':self.patient.age}

    @classmethod
    def write(cls, evaluations, vals):
        # Don't allow to write the record if the evaluation has been done
        if is_not_synchro():
            for ev in evaluations:
                if ev.state == 'done':
                    cls.raise_user_error(
                        "This evaluation is in a Done state.\n"
                        "You can no longer modify it.")
        return super(PatientEvaluation, cls).write(evaluations, vals)



class SignsAndSymptoms(ModelSQL, ModelView):
    'Evaluation Signs and Symptoms'
    __name__ = 'gnuhealth.signs_and_symptoms'

    sign_or_symptom = fields.Selection([
        (None, ''),
        ('sign', 'Sign'),
        ('symptom', 'Symptom')],
        'Subjective / Objective', required=False, 
        states={'invisible':True})

    @staticmethod
    def default_sign_or_symptom():
        return 'symptom'

