# -*- coding: utf-8 -*-
##############################################################################
#
#    GNU Health: The Free Health and Hospital Information System
#    Copyright (C) 2008-2014  GNU SOLIDARIO <health@gnusolidario.org>
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
#
# Localization module for Jamaica Ministry of Health
#
# The documentation of the module goes in the "doc" directory.

import string
import random
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['PartyPatient', 'AlternativePersonID', 'PostOffice',
    'DistrictCommunity', 'DomiciliaryUnit', 'Newborn', 'Insurance']
__metaclass__ = PoolMeta

_STATES = {
    'invisible': Not(Bool(Eval('is_person'))),
}
_DEPENDS = ['is_person']


class PartyPatient (ModelSQL, ModelView):
    'Party'
    __name__ = 'party.party'
    
    ref = fields.Char(
        'UPC',
        help='Universal Patient Code',
        states=_STATES, depends=_DEPENDS, readonly=True)
    alias = fields.Char('Alias', states=_STATES, depends=_DEPENDS,
        help="Common name that the Patient is referred to as")
    middlename = fields.Char('Middle Name', states=_STATES, depends=_DEPENDS,
        help="Middle name of Patient")
    mother_maiden_name = fields.Char('Mother Maiden Name', states=_STATES, 
        depends=_DEPENDS, help="Mother's Maiden Name")
    father_name = fields.Char('Father Name', states=_STATES, depends=_DEPENDS,
        help="Father's Name")

    suffix = fields.Selection([
        (None,''),
        ('jr', 'JR. - Junior'),
        ('sr', 'SR. - Senior'),
        ('II', 'II - The Second'),
        ('III', 'III - The Third'),
        ], 'Suffix', states=_STATES, depends=_DEPENDS)

    marital_status = fields.Selection([
        (None, ''),
        ('s', 'Single'),
        ('m', 'Married'),
        ('c', 'Concubinage'),
        ('w', 'Widowed'),
        ('d', 'Divorced'),
        ('x', 'Separated'),
        ('v', 'Visiting'),
        ], 'Marital Status', sort=False)

    """
    # To Be discussed : In GNU HEalthAmbiguous genitalia is used at birth as 
    # a finding.
    # Check legislation for Jamaica
    
    sex = fields.Selection([
        (None,''),
        ('m', 'Male'),
        ('f', 'Female'),
        ('u', 'Unknown')
        ], 'Sex', states={'required':Bool(Eval('is_person'))},
        help="Gender of Patient")

    """

    party_warning_ack = fields.Boolean('Party verified', 
        states={
            'invisible': Not(Bool(Eval('unidentified'))),
            'readonly': Bool(Eval('ref'))
            })

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


class AlternativePersonID (ModelSQL, ModelView):
    'Alternative person ID'
    __name__ ='gnuhealth.person_alternative_identification' 
   
    issuedby = fields.Selection(
        [
            (None,''),
            ('kph','KPH'),
            ('vjh','VJH'),
            ('crh','CRH'),            
        ], 'Issued By', required=False, sort=True,)

    @classmethod
    def __setup__(cls):
        super(AlternativePersonID, cls).__setup__()
        selections = [
                ('trn','TRN'),
                ('pathID','PATH ID'),
                ('gojID','GOJ ID'),
            ]
        for selection in selections:
            if selection not in cls.alternative_id_type.selection:
                cls.alternative_id_type.selection.append(selection)


class PostOffice(ModelSQL, ModelView):
    'Country Post Office'
    __name__ = 'country.post_office'
    
    name = fields.Char('Post Office', required=True, help="Post Offices")

    @classmethod
    def __setup__(cls):
        super(PostOffice, cls).__setup__()
        cls._sql_constraints = [
            ('name_uniq', 'UNIQUE(name)',
                'The Post Office must be unique !'),
        ]


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
            ('name_uniq', 'UNIQUE(name)',
                'The District Community must be unique !'),
        ]


class DomiciliaryUnit(ModelSQL, ModelView):
    'Domiciliary Unit'
    __name__ = 'gnuhealth.du'

    address_subdivision = fields.Many2One(
        'country.subdivision', 'Parish',
        domain=[('country', '=', Eval('address_country'))],
        depends=['address_country'], help="Enter Parish or State or County or Borrow")
    address_post_office = fields.Many2One(
        'country.post_office', 'Post Office', help="Enter Post Office")
    address_district_community = fields.Many2One(
        'country.district_community', 'District Community',
        domain=[('post_office', '=', Eval('address_post_office'))],
        depends=['address_post_office'], help="Enter District Community")


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
