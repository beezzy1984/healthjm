# -*- coding: utf-8 -*-
##############################################################################
#
#    Health-Jamaica: The Jamaica Electronic Patient Administration System
#    Copyright 2015  Ministry of Health (NHIN), Jamaica <admin@mohnhin.info>
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

import re
import random
import uuid
from datetime import date, datetime
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal, And, Or

ThisInstitution = lambda : Pool().get('gnuhealth.institution').get_institution()

from .tryton_utils import is_not_synchro

_DEPENDS = ['is_person']
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

NNre = re.compile('(%?)NN-(.*)', re.I)

_STATES = {
    'invisible': Not(Bool(Eval('is_person'))),
}

class PartyPatient(ModelSQL, ModelView):
    'Party'
    __name__ = 'party.party'

    upi = fields.Function(fields.Char('UPI', help='Unique Party Identifier'),
                          'get_upi_display', searcher='search_upi')
    firstname = fields.Char('First name', states=_STATES, depends=_DEPENDS,
        select=True)
    middlename = fields.Char('Middle Name', states=_STATES, depends=_DEPENDS,
        help="Middle name or names of Patient")
    maiden_name = fields.Char(
        'Maiden Name', 
        states={'invisible':Or(Not(Equal(Eval('marital_status'), 'm')),
                               Equal(Eval('sex'), 'm'))})
    mother_maiden_name = fields.Char("Mother's Maiden Name", states=_STATES, 
        depends=_DEPENDS, help="Mother's Maiden Name")
    father_name = fields.Char("Father's Name", states=_STATES,
                              depends=_DEPENDS, help="Father's Name")
    sex_display = fields.Function(fields.Char('Sex'), 'get_sex_display')

    # gender vs sex: According to the AMA Manual of Style :
    # Gender refers to the psychological/societal aspects of being male
    # or female, sex refers specifically to the physical aspects.
    # Do not interchange

    alt_ids = fields.Function(fields.Char('Alternate IDs'), 'get_alt_ids',
        searcher='search_alt_ids')
    marital_status_display = fields.Function(fields.Char('Marital Status'),
                                             'get_marital_status_display')

    @classmethod
    def __setup__(cls):
        super(PartyPatient, cls).__setup__()

        # Error Message
        cls._error_messages.update({
            'future_dob_error':
                '== Error ==\n\nDate of birth cannot be in the future.',
            'unidentified_party_warning':
                '== Indentity Verification ==\n\n'
                'Please enter an Alternative ID or leave Undentified checked.\n'
        })

        # field behaviour modifications
        s = cls.name.states if cls.name.states else {}
        s['readonly'] = Bool(Eval('is_person'))
        cls.name.states = s.copy()
        cls.ref.states['readonly'] = True
        cls.lastname.select = True
        cls.sex.selection = [(None, '')] + SEX_OPTIONS
        cls.marital_status.selection = [(None, '')] + MARITAL_STATUSES
        cls.internal_user.states = {
            'invisible': Not(Bool(Eval('is_healthprof'))),
            'required': False,
        }

        # field label modifications
        cls.ref.string = "UPI"
        cls.insurance.string = "Insurance Plans"

        # help text mods
        cls.ref.help = "Unique Party Indentifier"
        cls.alias.help = "Pet-name or other name by which party is known"
        cls.internal_user.help = ' '.join([
            'In order for this health professional to use'
            'the system, an internal user account must be assigned.'
            'This health professional will have a user account in this'
            'instance only.'])

    @classmethod
    def validate(cls, parties):
        super(PartyPatient, cls).validate(parties)
        for party in parties:
            party.check_dob()
            if is_not_synchro():
                party.check_party_warning()

    def check_dob(self):
        if self.dob and self.dob > date.today():
            self.raise_user_error('future_dob_error')

    def check_party_warning(self):
        '''validates that a party being entered as verified has an alt-id
        if there is no alt-id, then the party should be labeled as unidentified
        '''
        if len(self.alternative_ids) == 0 and not self.unidentified:
            self.raise_user_error('unidentified_or_altid')


    def get_rec_name(self, name):
        return self.name

    @staticmethod
    def default_alternative_identification():
        return True

    @staticmethod
    def default_unidentified():
        return False

    @fields.depends('lastname', 'firstname', 'middlename')
    def on_change_with_name(self, *arg, **kwarg):
        namelist = [self.lastname]
        if self.firstname:
            namelist = [''.join((self.lastname,',')), self.firstname]
        if self.middlename:
            namelist.append(self.middlename)
        return ' '.join(namelist)

    def get_upi_display(self, name):
        if self.is_patient and self.unidentified:
            return u'NN-{}'.format(self.ref)
        else:
            return self.ref

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

    def get_sex_display(self, field_name):
        sex_dict = dict(SEX_OPTIONS)
        return sex_dict.get(self.sex, '')

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
            return ['AND',('alternative_ids.alternative_id_type','=',
                           'medical_record'),
                    ('alternative_ids.code',)+tuple(clause[1:])]
        else:
            return ['AND',
            ('alternative_ids.alternative_id_type','!=','medical_record'),
            ('alternative_ids.code', clause[1], clause[2])]

    def get_marital_status_display(s,n):
        return make_selection_display()(s,'marital_status')

    @classmethod
    def generate_puid(cls):
        # Add a default random string in the ref field.
        # The STRSIZE constant provides the length of the HIN
        # The format of the UPC is XXXNNNXXX
        STRSIZE = 9
        letters = ('ABCDEFGHJKLMNPRTUWXY')
        digits = '0123456789'
        # letters removed = IOQSVZ because they look too similar to numbers
        # or to other letters.
        hin = ''
        for x in range(STRSIZE):
            if ( x < 3 or x > 5 ):
                hin = hin + random.choice(letters)
            else:
                hin = hin + random.choice(digits)
        return hin

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('party.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not 'ref' in values or not values['ref'] :
                values['ref'] = cls.generate_puid()
                if 'is_person' in values and not values['is_person']:
                    values['ref'] = 'NP-' + values['ref']

            if not values.get('code'):
                config = Configuration(1)
                # Use the company name . Initially, use the name
                # since the company hasn't been created yet.
                institution_id = ThisInstitution()
                if institution_id:
                    institution = Pool().get(
                            'gnuhealth.institution')(institution_id)
                    suffix = institution.code
                else:
                    suffix = Transaction().context.get('company.rec_name')\
                        or values['name']
                values['code'] = '-'.join([str(x) for x in
                                          (uuid.uuid4(), suffix)])
            values.setdefault('addresses', None)
        return super(PartyPatient, cls).create(vlist)


class AlternativePersonID (ModelSQL, ModelView):
    'Alternative person ID'
    __name__ ='gnuhealth.person_alternative_identification'

    issuing_institution = fields.Many2One('gnuhealth.institution', 'Issued By',
        help='Institution that assigned the medical record number',
        states={'required':Eval('alternative_id_type') == 'medical_record'},
        depends=['alternative_id_type'], select=True)
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

